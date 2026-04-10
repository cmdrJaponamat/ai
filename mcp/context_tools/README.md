# context-tools

Минимальный MCP/core слой поверх PostgreSQL базы `ai_context`.

DB-доступ теперь сделан через `psycopg`, по мотивам `CodexKnowledgeHelper`, а не через shell-вызовы `psql`.

Первый шаг специально узкий:

- читать проекты из `ai_context.projects`
- записывать snapshots в `ai_context.snapshots`
- читать snapshots по проекту
- строить минимальный kb projection из project docs

Это связывает уже существующие `phototrap-tools` и `ai-control` с новым контекстным хранилищем.

## Текущие инструменты

- `context-list-projects`
- `context-get-project`
- `context-list-snapshots`
- `context-record-snapshot`
- `kb-capture-project-bundle`
- `kb-bootstrap-projection`
- `kb-rebuild-project-projection`
- `kb-project-status`
- `kb-project-status-compact`
- `kb-get-project-overview`
- `kb-get-project-state`
- `kb-get-active-tasks`
- `kb-get-next-steps`
- `kb-get-decisions`
- `kb-get-constraints`
- `kb-get-source-refs`
- `kb-validate-projection`

## Быстрая проверка

```bash
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-projects
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py context-get-project Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-snapshots Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-bootstrap-projection Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-project-status Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-project-status-compact Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-active-tasks Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-project-overview Photo_Trap
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-next-steps Photo_Trap
```

## Конфигурация БД

По умолчанию используется:

```text
postgresql://japonamat@127.0.0.1/ai_context
```

При необходимости можно переопределить:

```text
AI_CONTEXT_DSN=postgresql://user@127.0.0.1/ai_context
AI_CONTEXT_CONNECT_TIMEOUT=10
```

## Следующий шаг

После проверки этого слоя можно:

1. добавлять snapshots из `phototrap_refactor_checkpoint`
2. добавлять индексируемые documents
3. добавлять `context_search`
