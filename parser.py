import re
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

URL = "https://www.youtube.com/watch?v=9HNczuxYxvw"
OUTPUT = "gpt_text.txt"


def extract_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else url[:11]


def main() -> None:
    video_id = extract_id(URL)
    print(f"[+] Видео ID: {video_id}")

    try:
        api = YouTubeTranscriptApi()
        # API 1.2.4: list() → find_transcript() → fetch()
        transcript = api.list(video_id).find_transcript(["en"])
        data = transcript.fetch()

        # Сохраняем каждую субтитровую строку отдельно (сохраняем \n)
        lines = [snippet.text for snippet in data]
        text = "\n".join(lines)

        Path(OUTPUT).write_text(text, encoding="utf-8")
        print(f"[OK] Сохранено: {OUTPUT} ({len(text)} симв., {len(data)} строк)")

    except Exception as err:
        print(f"[ERROR] {err}")
        raise


if __name__ == "__main__":
    main()
