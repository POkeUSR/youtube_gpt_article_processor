from youtube_transcript_api import YouTubeTranscriptApi
import json


def run_simple():
    video_id = "0lQIcwnyX48"  # вернем исходный ID
    print(f"--- Тест для видео {video_id} ---")

    try:
        # Самый базовый метод получения
        print("Запрос к YouTube...")
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])

        # Если мы здесь, значит данные получены
        print(f"Успех! Получено строк: {len(transcript)}")

        # Сохраняем только текст в одну строку
        full_text = " ".join([item.text for item in transcript])

        with open("gpt_text.txt", "w", encoding="utf-8") as f:
            f.write(full_text)

        print("Результат записан в файл gpt_text.txt")
        print("\nНачало текста:")
        print(full_text[:300] + "...")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        print("\nДоступные методы в вашей библиотеке:")
        # Это покажет, что вообще есть внутри установленного пакета
        import youtube_transcript_api

        print(dir(youtube_transcript_api.YouTubeTranscriptApi))


if __name__ == "__main__":
    run_simple()
