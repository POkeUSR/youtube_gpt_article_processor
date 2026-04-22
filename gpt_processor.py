"""
GPT Article Processor
Переводит текст статьи и создает краткую сводку с помощью OpenAI API.
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


# Загружаем .env при импорте модуля
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
    # Сводка всегда на русском
    SUMMARY_PROMPT = (
        "You are an expert analyst. Extract the 5-7 most important takeaways "
        "and main ideas from this article. Present them as a concise bulleted list "
        "in Russian. Keep each bullet point short and impactful."
    )
    TRANSLATION_PROMPT = (
        "You are a professional translator. Translate the following text into "
        "{language}. Maintain the original paragraph structure, formatting, and tone. "
        "Do not add explanations or comments."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        target_language: str = "ru",
    ):
        """
        Инициализация процессора.

        Args:
            api_key: OpenAI API ключ. Если None, берется из переменной окружения OPENAI_API_KEY.
            model: Модель OpenAI для использования (по умолчанию gpt-4o-mini)
            target_language: Целевой язык перевода (по умолчанию русский)
        """
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
        """Выполняет запрос к OpenAI API."""
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
        except openai.RateLimitError:
            raise RuntimeError("Превышен лимит запросов к OpenAI API")
        except openai.AuthenticationError:
            raise RuntimeError("Неверный API ключ OpenAI")
        except openai.APIConnectionError as e:
            raise RuntimeError(f"Ошибка подключения к OpenAI: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка API OpenAI: {e}")

    def translate(self, text: str, language: Optional[str] = None) -> str:
        """Переводит текст на указанный язык."""
        lang = language or self.target_language
        prompt = self.TRANSLATION_PROMPT.format(language=lang)
        return self._call_gpt(prompt, text, max_tokens=4000)

    def summarize(self, text: str) -> str:
        """Создает краткую сводку текста на русском."""
        return self._call_gpt(self.SUMMARY_PROMPT, text, max_tokens=1500)

    def process(
        self,
        text: str,
        output_dir: Optional[Path | str] = None,
        translate_to: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Полная обработка статьи: перевод + сводка.

        Args:
            text: Исходный текст статьи
            output_dir: Директория для сохранения результатов (по умолчанию текущая)
            translate_to: Целевой язык перевода

        Returns:
            ProcessingResult с результатами
        """
        if not text or not text.strip():
            raise ValueError("Текст статьи пуст")

        output_dir = Path(output_dir) if output_dir else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        target_lang = translate_to or self.target_language

        print(f"Перевод на {target_lang}...")
        translated = self.translate(text, language=target_lang)

        print("Создание сводки...")
        summary = self.summarize(text)  # всегда на русском

        result = ProcessingResult(
            original_text=text,
            translated_text=translated,
            summary_text=summary,
            target_language=target_lang,
        )

        # Сохраняем файлы
        (output_dir / "translated_article.txt").write_text(translated, encoding="utf-8")
        (output_dir / "summary_article.txt").write_text(summary, encoding="utf-8")

        print(f"[OK] Файлы сохранены в {output_dir}/")
        return result


def main():
    """Пример использования процессора."""
    import argparse

    parser = argparse.ArgumentParser(description="Обработка статьи: перевод + сводка")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path(__file__).parent / "gpt_text.txt",
        help="Входной файл с текстом статьи (по умолчанию: gpt_text.txt в папке скрипта)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Директория для сохранения результатов (по умолчанию: текущая)",
    )
    args = parser.parse_args()

    INPUT_FILE = args.input

    # 1. Проверяем существование файла
    if not INPUT_FILE.exists():
        print(
            f"Error: '{INPUT_FILE}' not found. Please create the file and add the article text.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Читаем текст
    try:
        text = INPUT_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Проверяем, что текст не пустой
    if not text.strip():
        print(
            f"Error: File '{INPUT_FILE}' is empty. Please add the article text.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 4. Обрабатываем
    try:
        processor = GPTArticleProcessor()
        result = processor.process(text, output_dir=args.output)

        print(f"\n--- Перевод ({result.target_language}) ---")
        print(result.translated_text[:300] + "...\n")
        print("--- Сводка ---")
        print(result.summary_text)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Читаем текст
    try:
        text = INPUT_FILE.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Проверяем, что текст не пустой
    if not text.strip():
        print(
            f"Error: File '{INPUT_FILE}' is empty. Please add the article text.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 4. Обрабатываем
    try:
        processor = GPTArticleProcessor()
        result = processor.process(text)

        print(f"\n--- Перевод ({result.target_language}) ---")
        print(result.translated_text[:300] + "...\n")
        print("--- Сводка ---")
        print(result.summary_text)

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
