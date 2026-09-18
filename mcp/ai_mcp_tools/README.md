# ai-mcp-tools

Project-level MCP/core слой для проекта `ai-control-plane` (`/home/japonamat/ai`).

Назначение: быстро проверять состояние MCP/PostgreSQL-инфраструктуры, recovery/doc sync и bootstrap readiness без ручного обхода файлов.

## Текущие инструменты

- `ai-mcp-status` - git status + latest commits + MCP server list
- `ai-mcp-read-recovery` - читает `/home/japonamat/ai/.ai-recovery.md`
- `ai-mcp-snapshot-audit` - проверяет Postgres projects/snapshots/projections и записывает snapshot в `ai_context`
- `ai-mcp-tooling-audit` - проверяет наличие MCP server dirs и ключевых файлов
- `ai-mcp-read-file <relative_path>` - читает файл внутри `/home/japonamat/ai`
- `ai-mcp-search <query>` - ищет по `/home/japonamat/ai` через `rg`

## Быстрая проверка

```bash
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_mcp_tools/cli.py ai-mcp-status
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_mcp_tools/cli.py ai-mcp-snapshot-audit
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_mcp_tools/cli.py ai-mcp-tooling-audit
```

## Запуск MCP-сервера

```bash
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_mcp_tools/server.py
```

