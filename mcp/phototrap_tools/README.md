# phototrap-tools

Минимальный project-level MCP/core слой для `Photo_Trap`.

Этот шаг дает отдельные инструменты проекта, чтобы не ходить к нему через общий shell каждый раз.

Аудит-инструменты теперь автоматически сохраняют свои результаты в `ai_context.snapshots`, чтобы повторный заход в проект не требовал каждый раз заново пересчитывать одни и те же отчеты.

Сейчас слой состоит из двух частей:

- `tools.py` и `cli.py` для локальной проверки;
- `server.py` как MCP stdio-сервер.

## Текущие инструменты

- `phototrap-status` - краткий git status проекта
- `phototrap-read-recovery` - читает `.ai-recovery.md` проекта
- `phototrap-safe-split-audit` - аудит крупных `.kt` файлов и лимита `700`
- `phototrap-refactor-checkpoint` - `git status` + крупные `.kt` + лимит + `assembleDebug`
- `phototrap-recovery-sync-audit` - какие архитектурные коммиты еще не отражены в recovery/TODO
- `phototrap-module-seam-check` - где уже есть seam-like зависимости и где остались жесткие concrete deps
- `phototrap-read-file <relative_path>` - читает конкретный файл внутри проекта
- `phototrap-search-code <query>` - ищет текст по проекту через `rg`

## Быстрая проверка

```bash
python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-status
python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-read-recovery
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-safe-split-audit --top-n 10
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-refactor-checkpoint --top-n 8
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-recovery-sync-audit --limit 12
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-module-seam-check --top-n 10
python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-search-code cleanup --limit 5
python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-read-file app/src/main/java/com/cmdrjaponamat/phototrap/camera/MediaIndexRepository.kt
```

## Запуск MCP-сервера

```bash
/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/phototrap_tools/server.py
```

Пример MCP-конфига:

```toml
[mcp_servers.phototrap-tools]
command = "/home/japonamat/ai/mcp/.venv/bin/python3"
args = ["/home/japonamat/ai/mcp/phototrap_tools/server.py"]
```

## Следующий шаг

После проверки core можно:

1. добавить безопасные gradle/git инструменты
2. подключить LightRAG индекс для `Photo_Trap`
3. затем связать `ai-control` и `phototrap-tools` в одном клиенте
