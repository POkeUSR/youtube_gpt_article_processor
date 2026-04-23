from youtube_transcript_api import YouTubeTranscriptApi

video_id = ""

print("=== ВСЕ ДОСТУПНЫЕ СУБТИТРЫ ===")
for transcript in YouTubeTranscriptApi.list_transcripts(video_id):
    print(
        f"  [{transcript.language_code}] {transcript.language} "
        f"(авто: {transcript.is_generated}, переводим: {transcript.is_translatable})"
    )

print("\n=== ЗАБИРАЕМ ВСЕ ПОЛЬЗУЮЩИЕСЯ ЯЗЫКИ ===")
# Собираем, какие языки можно запросить через fetch
for transcript in YouTubeTranscriptApi.list_transcripts(video_id):
    if transcript.language_code not in ["en"]:
        try:
            text = " ".join([t.text for t in transcript.fetch()])
            with open(
                f"text_{transcript.language_code}.txt", "w", encoding="utf-8"
            ) as f:
                f.write(text)
            print(f"  Сохранено: text_{transcript.language_code}.txt")
        except Exception as e:
            print(f"  Не удалось: {e}")
    else:
        print(f"  [{transcript.language_code}] уже был забран")
