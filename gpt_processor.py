"""
GPT Article Processor.
Переводит текст статьи и создаёт краткую сводку с помощью OpenAI API.
Поддерживает длинные тексты через chunking.
"""

from __future__ import annotations

import os
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import openai
from dotenv import load_dotenv


load_dotenv()


@dataclass
class ProcessingResult:
    """Результат обработки статьи."""

    original_text: str
    translated_text: str
    summary_text: str
    source_language: Optional[str] = None
    target_language: str = "ru"


class GPTArticleProcessor:
    """Обработчик статей с помощью GPT для перевода и суммирования."""

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_CHARS_PER_CHUNK = 6000  # ~1500-2000 токенов

    SUMMARY_PROMPT: str = (
        "You are an expert analyst. Extract the 5-7 most important takeaways "
        "and main ideas from this article. Present them as a concise bulleted list "
        "in Russian. Keep each bullet point short and impactful."
    )
    TRANSLATION_PROMPT: str = (
        "You are a professional translator. Translate the following text into "
        "{language}. Maintain the original paragraph structure, formatting, and tone. "
        "Do not add explanations or comments. Translate COMPLETELY without truncation."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        target_language: str = "ru",
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY не найден. Укажите API ключ в .env файле "
                "или передайте его в параметр api_key."
            )
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.target_language = target_language

    def _call_gpt(self, prompt: str, text: str, max_tokens: int = 2000) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError as err:
            raise RuntimeError("Превышен лимит запросов к OpenAI API") from err
        except openai.AuthenticationError as err:
            raise RuntimeError("Неверный API ключ OpenAI") from err
        except openai.APIConnectionError as err:
            raise RuntimeError(f"Ошибка подключения к OpenAI: {err}") from err
        except Exception as err:
            raise RuntimeError(f"Ошибка API OpenAI: {err}") from err

    def _split_into_chunks(self, text: str, max_chars: int) -> list[str]:
        """Разбивает текст на блоки по границам абзацев."""
        import re

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) > max_chars:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if current and len(" ".join(current) + " " + sent) > max_chars:
                        chunks.append("\n\n".join(current))
                        current = [sent]
                    else:
                        current.append(sent)
            else:
                if current and len("\n\n".join(current) + "\n\n" + para) > max_chars:
                    chunks.append("\n\n".join(current))
                    current = [para]
                else:
                    current.append(para)

        if current:
            chunks.append("\n\n".join(current))
        return chunks

    def translate(self, text: str, language: Optional[str] = None) -> str:
        """Переводит текст. Если длинный — разбивает на чанки."""
        lang = language or self.target_language
        prompt = self.TRANSLATION_PROMPT.format(language=lang)

        if len(text) <= self.MAX_CHARS_PER_CHUNK:
            return self._call_gpt(prompt, text, max_tokens=4000)

        chunks = self._split_into_chunks(text, self.MAX_CHARS_PER_CHUNK)
        print(f"  [INFO] Текст разбит на {len(chunks)} частей")

        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Перевод части {i}/{len(chunks)}... ({len(chunk)} симв.)")
            part = self._call_gpt(prompt, chunk, max_tokens=4000)
            parts.append(part)

        return "\n\n".join(parts)

    def summarize(self, text: str) -> str:
        """Создаёт сводку. Для длинных текстов использует начало и конец."""
        if len(text) > 20000:
            words = text.split()
            first = " ".join(words[:6000])
            last = " ".join(words[-6000:])
            combined = (
                f"{first}\n\n... (пропущено {len(words) - 12000} слов) ...\n\n{last}"
            )
            return self._call_gpt(self.SUMMARY_PROMPT, combined, max_tokens=1500)
        return self._call_gpt(self.SUMMARY_PROMPT, text, max_tokens=1500)

    def process(
        self,
        text: str,
        output_dir: Optional[Path | str] = None,
        translate_to: Optional[str] = None,
    ) -> ProcessingResult:
        if not text or not text.strip():
            raise ValueError("Текст статьи пуст")

        output_dir = Path(output_dir) if output_dir else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        target_lang = translate_to or self.target_language

        print(f"Перевод на {target_lang}...")
        translated = self.translate(text, language=target_lang)

        print("Создание сводки...")
        summary = self.summarize(text)

        result = ProcessingResult(
            original_text=text,
            translated_text=translated,
            summary_text=summary,
            target_language=target_lang,
        )

        (output_dir / "translated_article.txt").write_text(translated, encoding="utf-8")
        (output_dir / "summary_article.txt").write_text(summary, encoding="utf-8")

        print(f"[OK] Файлы сохранены в {output_dir}/")
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Обработка статьи: перевод + сводка")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path(__file__).parent / "gpt_text.txt",
        help="Входной файл (по умолчанию: gpt_text.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Директория для сохранения (по умолчанию: текущая)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        text = args.input.read_text(encoding="utf-8")
    except Exception as err:
        print(f"Error reading file: {err}", file=sys.stderr)
        sys.exit(1)

    if not text.strip():
        print(f"Error: файл '{args.input}' пуст.", file=sys.stderr)
        sys.exit(1)

    try:
        processor = GPTArticleProcessor()
        result = processor.process(text, output_dir=args.output)

        print(f"\n--- Перевод ({result.target_language}) ---")
        print(result.translated_text[:300] + "...\n")
        print("--- Сводка ---")
        print(result.summary_text)

    except Exception as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
