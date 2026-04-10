# context-tools

Минимальный MCP/core слой поверх PostgreSQL базы `ai_context`.

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
- `kb-get-project-overview`
- `kb-get-project-state`
- `kb-get-next-steps`
- `kb-get-decisions`
- `kb-get-constraints`
- `kb-get-source-refs`
- `kb-validate-projection`

## Быстрая проверка

```bash
python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-projects
python3 /home/japonamat/ai/mcp/context_tools/cli.py context-get-project Photo_Trap
python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-snapshots Photo_Trap
python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-bootstrap-projection Photo_Trap
python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-project-overview Photo_Trap
python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-next-steps Photo_Trap
```

## Следующий шаг

После проверки этого слоя можно:

1. добавлять snapshots из `phototrap_refactor_checkpoint`
2. добавлять индексируемые documents
3. добавлять `context_search`
