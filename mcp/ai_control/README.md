# ai-control

Минимальное локальное ядро для будущего MCP-сервера вокруг `~/ai`.

Сейчас слой состоит из двух частей:

- `tools.py` и `cli.py` для локальной проверки логики;
- `server.py` как настоящий MCP stdio-сервер поверх того же core.

## Текущие инструменты

- `list-projects` - читает `PROJECT_CONTEXTS.md`
- `read-project-recovery <name>` - возвращает recovery указанного проекта
- `search-recovery <query>` - ищет совпадения по `~/ai/recovery/*.md`
- `search-actions-log <query>` - ищет совпадения по `~/ai/actions.log`
- `append-actions-log --what ... --why ... --verification ... [--rollback ...] [--relogin ...]`

## Быстрая проверка

```bash
python3 /home/japonamat/ai/mcp/ai_control/cli.py list-projects
python3 /home/japonamat/ai/mcp/ai_control/cli.py read-project-recovery Photo_Trap
python3 /home/japonamat/ai/mcp/ai_control/cli.py search-recovery Photo_Trap
python3 /home/japonamat/ai/mcp/ai_control/cli.py search-actions-log github-auto
```

## Запуск MCP-сервера

Локальное окружение:

```bash
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_control/server.py
```

Пример MCP-конфига для клиента:

```json
{
  "mcpServers": {
    "ai-control": {
      "command": "/home/japonamat/ai/mcp/.venv/bin/python3",
      "args": [
        "/home/japonamat/ai/mcp/ai_control/server.py"
      ]
    }
  }
}
```

## Следующий шаг

После проверки этого ядра можно:

1. подключить отдельный индекс LightRAG для `~/ai`
2. затем сделать отдельный `phototrap-tools`
3. после этого связать `ai-control` и `phototrap-tools` в одном клиенте
