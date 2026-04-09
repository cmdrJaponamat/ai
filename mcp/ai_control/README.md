# ai-control

Минимальное локальное ядро для будущего MCP-сервера вокруг `~/ai`.

Первый шаг специально сделан без transport-слоя:

- логика инструментов живет отдельно;
- ее можно проверить обычным `python3`;
- потом поверх нее можно добавить настоящий MCP server без переписывания core.

## Текущие инструменты

- `list-projects` - читает `PROJECT_CONTEXTS.md`
- `read-project-recovery <name>` - возвращает recovery указанного проекта
- `append-actions-log --what ... --why ... --verification ... [--rollback ...] [--relogin ...]`

## Быстрая проверка

```bash
python3 /home/japonamat/ai/mcp/ai_control/cli.py list-projects
python3 /home/japonamat/ai/mcp/ai_control/cli.py read-project-recovery Photo_Trap
```

## Следующий шаг

После проверки этого ядра можно:

1. добавить поиск по `~/ai/recovery`
2. добавить MCP transport
3. подключить отдельный индекс LightRAG для `~/ai`
