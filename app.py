"""
Flask Web App для обработки YouTube видео.
Принимает ссылку → загружает субтитры → переводит и суммаризирует → возвращает файлы.
"""

from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_file
import re
import sys

try:
    from youtube_transcript_api import (
        YouTubeTranscriptApi,
        NoTranscriptFound,
        IpBlocked,
    )
except ImportError:
    YouTubeTranscriptApi = None

try:
    from gpt_processor import GPTArticleProcessor
except ImportError:
    GPTArticleProcessor = None

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Processor</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 500px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 24px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input[type="text"] {
            width: 100%;
            padding: 14px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.2s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
            display: none;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .alarm {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #f5c6cb;
            margin-bottom: 20px;
            display: none;
        }
        .alarm.warning {
            background: #fff3cd;
            color: #856404;
            border-color: #ffeaa7;
        }
        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 8px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .download-links {
            margin-top: 15px;
        }
        .download-links a {
            display: block;
            padding: 12px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-bottom: 10px;
            text-decoration: none;
            color: #333;
            transition: background 0.2s;
        }
        .download-links a:hover {
            background: #f8f9fa;
            border-color: #667eea;
        }
        .download-links a:last-child {
            margin-bottom: 0;
        }
        .icon {
            margin-right: 8px;
        }
        .info {
            font-size: 12px;
            color: #888;
            text-align: center;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube Transcript Processor</h1>
        
        <div class="alarm" id="alarm"></div>

        <form id="form">
            <div class="form-group">
                <label for="url">Ссылка на YouTube видео:</label>
                <input type="text" id="url" name="url" 
                       placeholder="https://www.youtube.com/watch?v=..." 
                       required>
            </div>
            <button type="submit" id="submitBtn">🚀 Обработать</button>
        </form>

        <div class="loader" id="loader"></div>

        <div class="result" id="result"></div>

        <div class="info">
            Поддерживаются видео с субтитрами на английском языке.
        </div>
    </div>

    <script>
        document.getElementById('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('url').value.trim();
            const btn = document.getElementById('submitBtn');
            const loader = document.getElementById('loader');
            const resultDiv = document.getElementById('result');
            const alarmDiv = document.getElementById('alarm');

            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                showAlarm('Пожалуйста, введите корректную ссылку на YouTube видео', false);
                return;
            }

            btn.disabled = true;
            loader.style.display = 'block';
            resultDiv.style.display = 'none';
            alarmDiv.style.display = 'none';

            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();

                if (response.ok && data.status === 'done') {
                    resultDiv.innerHTML = `
                        <h3>✅ Готово!</h3>
                        <div class="download-links">
                            <a href="${data.translated_url}" target="_blank">
                                <span class="icon">📄</span>Скачать перевод (translated_article.txt)
                            </a>
                            <a href="${data.summary_url}" target="_blank">
                                <span class="icon">📋</span>Скачать сводку (summary_article.txt)
                            </a>
                        </div>
                    `;
                    resultDiv.className = 'result success';
                } else {
                    let alarmMsg = data.message || 'Произошла ошибка';
                    let isWarning = false;
                    
                    if (data.error_type === 'youtube_blocked') {
                        isWarning = true;
                    }
                    
                    showAlarm(alarmMsg, isWarning);
                }
            } catch (err) {
                showAlarm('Сетевая ошибка: ' + err.message, false);
            } finally {
                btn.disabled = false;
                loader.style.display = 'none';
                resultDiv.style.display = 'block';
            }
        });

        function showAlarm(msg, isWarning) {
            const alarmDiv = document.getElementById('alarm');
            alarmDiv.textContent = (isWarning ? '⚠️ ' : '❌ ') + msg;
            alarmDiv.className = isWarning ? 'alarm warning' : 'alarm';
            alarmDiv.style.display = 'block';
            setTimeout(() => { alarmDiv.style.display = 'none'; }, 10000);
        }
    </script>
</body>
</html>"""


def extract_video_id(url_or_id: str) -> str:
    """Извлекает YouTube video ID из URL или возвращает как есть."""
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if len(url_or_id) == 11 and re.match(r"^[a-zA-Z0-9_-]+$", url_or_id):
        return url_or_id
    raise ValueError(f"Invalid YouTube URL or ID: {url_or_id}")


@app.route("/")
def index():
    """Главная страница с формой."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/process", methods=["POST"])
def process():
    """
    Основной endpoint обработки.
    Принимает JSON: {"url": "https://youtube.com/..."}
    Возвращает JSON: {"status": "done", "translated_url": "...", "summary_url": "..."}
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify(
            {
                "status": "error",
                "error_type": "validation",
                "message": "URL is required",
            }
        ), 400

    if YouTubeTranscriptApi is None or GPTArticleProcessor is None:
        return jsonify(
            {
                "status": "error",
                "error_type": "server",
                "message": "Server dependencies not installed",
            }
        ), 500

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        return jsonify(
            {"status": "error", "error_type": "invalid_url", "message": str(e)}
        ), 400

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    translated_file = out_dir / f"translated_{video_id}.txt"
    summary_file = out_dir / f"summary_{video_id}.txt"

    try:
        # 1. Получаем субтитры
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)

            try:
                transcript = transcript_list.find_transcript(["en"])
            except NoTranscriptFound:
                transcript = list(transcript_list)[0]

            snippets = transcript.fetch()
            text = "\n".join(snippet.text for snippet in snippets)

        except IpBlocked:
            return jsonify(
                {
                    "status": "error",
                    "error_type": "youtube_blocked",
                    "message": "YouTube заблокировал запрос с вашего IP. "
                    "Возможные причины: слишком много запросов, облачный провайдер. "
                    "Попробуйте позже или используйте VPN.",
                }
            ), 403
        except Exception as e:
            return jsonify(
                {
                    "status": "error",
                    "error_type": "youtube_error",
                    "message": f"Ошибка при получении субтитров: {str(e)}",
                }
            ), 500

        # 2. Обработка через GPT
        try:
            processor = GPTArticleProcessor()
            translated = processor.translate(text)
            summary = processor.summarize(text)
        except ValueError as e:
            if "OPENAI_API_KEY" in str(e):
                return jsonify(
                    {
                        "status": "error",
                        "error_type": "config",
                        "message": "Ошибка конфигурации: не задан OPENAI_API_KEY. "
                        "Проверьте файл .env",
                    }
                ), 500
            raise
        except Exception as e:
            return jsonify(
                {
                    "status": "error",
                    "error_type": "gpt_error",
                    "message": f"Ошибка при обработке GPT: {str(e)}",
                }
            ), 500

        # 3. Сохраняем файлы
        translated_file.write_text(translated, encoding="utf-8")
        summary_file.write_text(summary, encoding="utf-8")

        return jsonify(
            {
                "status": "done",
                "message": "Success",
                "translated_url": f"/download/{translated_file.name}",
                "summary_url": f"/download/{summary_file.name}",
                "video_id": video_id,
            }
        )

    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "error_type": "unknown",
                "message": f"Неожиданная ошибка: {str(e)}",
            }
        ), 500


@app.route("/download/<filename>")
def download(filename):
    """Скачивание файла."""
    file_path = Path("output") / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(
        str(file_path),
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain; charset=utf-8",
    )


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    if YouTubeTranscriptApi is None:
        print(
            "ERROR: youtube-transcript-api not installed. Run: pip install -r requirements.txt"
        )
        sys.exit(1)
    if GPTArticleProcessor is None:
        print(
            "ERROR: gpt_processor module not found. Make sure gpt_processor.py is in the same directory."
        )
        sys.exit(1)

    print("Starting YouTube Transcript Processor...")
    print("Open browser: http://localhost:5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
