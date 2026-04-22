import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

URL = "https://www.youtube.com/watch?v=2ZKLaUbB33o"
OUTPUT = "gpt_text.txt"

# 1. Извлекаем video_id из URL
m = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", URL)
video_id = m.group(1) if m else URL[:11]

# 2. Загружаем английские субтитры
transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
text = " ".join(t.text for t in transcript)

# 3. Сохраняем
Path(OUTPUT).write_text(text, encoding="utf-8")
print(f"Сохранено: {OUTPUT} ({len(text)} символов)")
