# LightRAG Bootstrap

Минимальный локальный bootstrap для индексов памяти вокруг `~/ai` и дальше `Photo_Trap`.

Первый шаг в этой директории поднимает только `ai_index`:

- отдельное Python-окружение
- конфиг под Ollama
- список источников
- скрипт сборки индекса
- скрипт query

## Текущее состояние

Сейчас структура готова, но индексация зависит от локального Ollama:

- сервер должен отвечать на `http://127.0.0.1:11434`
- должна быть LLM-модель для entity extraction
- должна быть embedding-модель

По умолчанию bootstrap ожидает:

- `qwen2.5:1.5b`
- `bge-m3:latest`

## Структура

```text
/home/japonamat/ai/lightrag/
  .venv/
  README.md
  requirements.txt
  ai_index/
    config.json
    sources.json
  scripts/
    common.py
    build_ai_index.py
    query_ai_index.py
```

## Установка окружения

```bash
python3 -m venv /home/japonamat/ai/lightrag/.venv
/home/japonamat/ai/lightrag/.venv/bin/pip install -r /home/japonamat/ai/lightrag/requirements.txt
```

## Подготовка Ollama

Запустить сервер:

```bash
ollama serve
```

Скачать модели:

```bash
ollama pull qwen2.5:1.5b
ollama pull bge-m3:latest
```

## Dry Run

Проверка конфигурации и списка файлов без индексации:

```bash
/home/japonamat/ai/lightrag/.venv/bin/python /home/japonamat/ai/lightrag/scripts/build_ai_index.py --dry-run
```

## Сборка индекса

```bash
/home/japonamat/ai/lightrag/.venv/bin/python /home/japonamat/ai/lightrag/scripts/build_ai_index.py --rebuild
```

## Query

```bash
/home/japonamat/ai/lightrag/.venv/bin/python /home/japonamat/ai/lightrag/scripts/query_ai_index.py "Что у меня по github-auto?"
```

## Следующий шаг

После первого успешного `ai_index`:

1. добавить query-tool в `ai-control`
2. поднять отдельный `phototrap_index`
3. затем связать `LightRAG` query с MCP tools
