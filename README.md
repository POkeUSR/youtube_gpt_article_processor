# GPT Article Processor

Модуль для автоматической обработки текстовых статей с помощью OpenAI GPT. Автоматически переводит статьи и создает краткие сводки.

## Возможности

- **Перевод**: Полный перевод статьи на любой язык с сохранением структуры
- **Суммирование**: Извлечение 5-7 ключевых тезисов в виде маркированного списка **на русском языке**
- **Автоматическое сохранение**: Результаты сохраняются в `translated_article.txt` и `summary_article.txt`
- **Гибкая настройка**: Выбор модели, языка перевода, директории вывода

## Настройка

### Установка зависимостей

**Windows:**
```cmd
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
pip install -r requirements.txt
```

### Настройка API ключа

**Windows:**
```cmd
copy .env.example .env
# Отредактируйте .env в любом текстовом редакторе, вставьте ваш OPENAI_API_KEY
```

**Linux/Mac:**
```bash
cp .env.example .env
# Отредактируйте .env, вставьте ваш OPENAI_API_KEY
```

### Подготовка файла с текстом

Создайте файл `gpt_text.txt` в папке со скриптом и поместите в него текст статьи.

**Или используйте парсер для YouTube субтитров:**
```bash
python parser.py  # Скачает субтитры и сохранит в gpt_text.txt
```

## Быстрый старт

### Подготовка файла

Создайте файл `gpt_text.txt` **в той же папке, что и скрипт** `gpt_processor.py`, и поместите в него текст статьи:

```
The Rise of Artificial Intelligence: What You Need to Know

Artificial intelligence is no longer science fiction. It's here...
```

### Базовое использование

**Windows:**
```cmd
# Запуск с файлом gpt_text.txt (ищется в папке со скриптом)
python gpt_processor.py

# Указать свой файл и папку вывода
python gpt_processor.py -i my_article.txt -o results/

# Или используйте run_processor.bat для запуска веб-сервера с браузером
run_processor.bat
```

**Linux/Mac:**
```bash
# Запуск с файлом gpt_text.txt (ищется в папке со скриптом)
python gpt_processor.py

# Указать свой файл и папку вывода
python gpt_processor.py -i my_article.txt -o results/
```

### В коде

```python
from gpt_processor import GPTArticleProcessor

# Читаем файл
from pathlib import Path
text = Path('gpt_text.txt').read_text(encoding='utf-8')

processor = GPTArticleProcessor()
result = processor.process(text, output_dir='output/')
# Файлы: output/translated_article.txt, output/summary_article.txt
```

## Настройки

### Конструктор класса

```python
GPTArticleProcessor(
    api_key=None,           # API ключ (если None, берется из .env)
    model="gpt-4o-mini",   # модель: gpt-4o-mini, gpt-4o, gpt-4-turbo
    target_language="ru"   # язык перевода по умолчанию
)
```

### Параметры метода `process()`

```python
result = processor.process(
    text="Текст статьи...",
    output_dir=Path("результаты/"),  # папка для сохранения
    translate_to="es"                # перевести на испанский
)
```

## Веб-интерфейс

Для удобства использования доступен веб-интерфейс на Flask:

```bash
python app.py
```

Затем откройте браузер: http://localhost:5000

**Windows:**
```cmd
run_processor.bat  # Запускает сервер и открывает браузер автоматически
```

Веб-интерфейс позволяет:
- Ввести ссылку на YouTube видео
- Автоматически скачать субтитры
- Перевести текст и создать сводку через GPT
- Скачать результаты в виде файлов

## Структура проекта

```
youtube/
├── app.py                # Веб-интерфейс Flask
├── gpt_processor.py      # Основной модуль обработки
├── parser.py             # Парсер YouTube субтитров
├── test.py               # Тест API
├── run_processor.bat     # Скрипт запуска для Windows
├── requirements.txt       # Зависимости
├── .env.example          # Пример конфигурации
├── .env                  # Ваш конфиг (НЕ коммитить!)
├── README.md             # Этот файл
└── output/               # Папка для результатов (создается автоматически)
```

## API Использование

### Класс `GPTArticleProcessor`

**Методы:**
- `translate(text, language=None)` — перевод текста
- `summarize(text)` — создание сводки (всегда на русском)
- `process(text, output_dir=None, translate_to=None)` — полная обработка

**Возвращает:** `ProcessingResult` с полями:
- `original_text` — исходный текст
- `translated_text` — переведенный текст
- `summary_text` — сводка-список
- `target_language` — язык перевода

## Обработка ошибок

```python
from gpt_processor import GPTArticleProcessor
from dotenv import dotenv_values

try:
    processor = GPTArticleProcessor()
    result = processor.process(article_text)
except ValueError as e:
    print(f"Ошибка конфигурации: {e}")
except RuntimeError as e:
    print(f"Ошибка API: {e}")
```

Распознаваемые ошибки:
- `ValueError` — пустой текст, отсутствует API ключ
- `RuntimeError` — ошибки API (лимиты, подключение, авторизация)

## Безопасность

- **Никогда не хардкодите API ключ** — используйте `.env` файл
- Добавьте `.env` в `.gitignore`:
  ```
  # .gitignore
  .env
  __pycache__/
  *.pyc
  ```
- Потребуйте минимальные права API ключа (только chat completions)

## Тонкая настройка

### Смена промптов

```python
class CustomProcessor(GPTArticleProcessor):
    SUMMARY_PROMPT = "Ваш кастомный промпт для сводки..."
    TRANSLATION_PROMPT = "Ваш промпт для перевода..."
```

### Пакетная обработка

```python
from pathlib import Path

processor = GPTArticleProcessor()

for article_file in Path("articles/").glob("*.txt"):
    text = article_file.read_text(encoding="utf-8")
    result = processor.process(text, output_dir=f"output/{article_file.stem}")
    print(f"Обработано: {article_file.name}")
```

## Требования

- Python 3.8+
- OpenAI API ключ (платный аккаунт)
- Пакеты: `openai`, `python-dotenv`

## Лицензия

MIT
