"""Тест chunking без вызова API."""

from gpt_processor import GPTArticleProcessor

proc = GPTArticleProcessor(api_key="dummy")  # не будем вызывать API

# Длинный текст (имитация)
with open("gpt_text.txt", encoding="utf-8") as f:
    text = f.read()

print(f"Текст: {len(text)} симв., ~{len(text.split())} слов")

# Проверяем разбивку
chunks = proc._split_into_chunks(text, max_chars=6000)
print(f"Чанков: {len(chunks)}")
print(f"Первый чанк: {len(chunks[0])} симв.")
print(f"Последний чанк: {len(chunks[-1])} симв.")

# Проверим, что суммарная длина чанков покрывает весь текст
total = sum(len(c) for c in chunks)
print(f"Сумма чанков: {total} (должно быть ~{len(text)})")
print("Ratio:", total / len(text))