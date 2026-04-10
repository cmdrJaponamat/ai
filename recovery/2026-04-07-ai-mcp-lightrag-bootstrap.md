# AI MCP + LightRAG Bootstrap

## problem_statement

Нужно начать внедрение локальной связки `MCP + LightRAG` вокруг `~/ai` и проекта `Photo_Trap` маленькими шагами, чтобы не потерять логику системы.

## findings

- `~/ai` уже выступает control plane для system work и recovery trail.
- `Photo_Trap` уже имеет качественный `.ai-recovery.md`, который подходит как первый source of truth для проектной памяти.
- Для первого шага не нужен полный MCP transport: достаточно отделить core-логику инструментов от будущей transport-обертки.

## exact_changes_made

- Добавлен каркас `/home/japonamat/ai/mcp/ai_control/`.
- Добавлен `README.md` с ролью первого шага и командами проверки.
- Добавлен `tools.py` с минимальными инструментами:
  - чтение индекса проектов из `PROJECT_CONTEXTS.md`
  - чтение project recovery по имени проекта
  - запись в `actions.log`
- Добавлен `cli.py` для локальной проверки без внешнего MCP SDK.
- Во втором шаге добавлен минимальный поисковый слой без LightRAG:
  - `search-recovery <query>` для поиска по `~/ai/recovery/*.md`
  - `search-actions-log <query>` для поиска по `~/ai/actions.log`
- В третьем шаге добавлен настоящий MCP stdio transport:
  - локальный venv в `/home/japonamat/ai/mcp/.venv`
  - `mcp==1.27.0` в `/home/japonamat/ai/mcp/requirements.txt`
  - `/home/japonamat/ai/mcp/ai_control/server.py` на `FastMCP`
  - `.gitignore` обновлен для исключения `mcp/.venv/`
- MCP-сервер публикует инструменты:
  - `list_projects`
  - `read_project_recovery`
  - `search_recovery`
  - `search_actions_log`
  - `append_actions_log`
- В четвертом шаге добавлен отдельный project-level слой `/home/japonamat/ai/mcp/phototrap_tools/`:
  - `tools.py` и `cli.py` с базовыми операциями по `Photo_Trap`
  - `server.py` на `FastMCP`
  - сервер зарегистрирован в `~/.codex/config.toml` как `phototrap-tools`
- `phototrap-tools` публикует инструменты:
  - `phototrap_status`
  - `phototrap_read_recovery`
  - `phototrap_read_file`
  - `phototrap_search_code`
- Затем `phototrap-tools` был расширен двумя повторяющимися инженерными командами:
  - `phototrap_safe_split_audit`
  - `phototrap_refactor_checkpoint`
- `phototrap_safe_split_audit` дает:
  - топ крупных `.kt`
  - текущий лимит
  - список файлов выше лимита
  - список крупнейших файлов, которые уже в лимите
- `phototrap_refactor_checkpoint` дает:
  - `git status`
  - branch
  - топ крупных `.kt`
  - подсветку файлов выше лимита
  - результат `./gradlew assembleDebug`
- В пятом шаге добавлен bootstrap `LightRAG` для `~/ai`:
  - `/home/japonamat/ai/lightrag/requirements.txt` с `lightrag-hku==1.4.13`
  - отдельное окружение `/home/japonamat/ai/lightrag/.venv`
  - конфиг `/home/japonamat/ai/lightrag/ai_index/config.json`
  - список источников `/home/japonamat/ai/lightrag/ai_index/sources.json`
  - bootstrap/query-скрипты в `/home/japonamat/ai/lightrag/scripts/`
  - `.gitignore` обновлен для исключения `lightrag/.venv/` и index storage
- Для первого индекса выбраны источники `~/ai`:
  - `WORKFLOW.md`
  - `ASSISTANT_BOOTSTRAP.md`
  - `PROJECT_CONTEXTS.md`
  - `actions.log`
  - `~/ai/recovery/*.md`
- По умолчанию bootstrap ожидает локальный Ollama:
  - LLM: `qwen2.5:1.5b`
  - embeddings: `bge-m3:latest`

## verification_status

- `python3 /home/japonamat/ai/mcp/ai_control/cli.py list-projects` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py read-project-recovery Photo_Trap` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py search-recovery Photo_Trap --limit 5` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py search-actions-log github-auto --limit 5` отработал успешно.
- Импорт `server.py` подтверждает регистрацию MCP tools:
  - `list_projects`
  - `read_project_recovery`
  - `search_recovery`
  - `search_actions_log`
  - `append_actions_log`
- Быстрый запуск `timeout 2 /home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_control/server.py` завершился без ошибки; в таком тесте stdio-сервер корректно выходит после закрытия stdin.
- `python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-status` отработал успешно.
- `python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-read-recovery` отработал успешно.
- `python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-search-code cleanup --limit 5` отработал успешно.
- `python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-safe-split-audit --top-n 8` отработал успешно.
- `python3 /home/japonamat/ai/mcp/phototrap_tools/cli.py phototrap-refactor-checkpoint --top-n 6` отработал успешно и вернул успешный `assembleDebug`.
- Импорт `/home/japonamat/ai/mcp/phototrap_tools/server.py` подтверждает регистрацию MCP tools:
  - `phototrap_status`
  - `phototrap_read_recovery`
  - `phototrap_read_file`
  - `phototrap_search_code`
- Импорт `/home/japonamat/ai/mcp/phototrap_tools/server.py` также подтверждает регистрацию:
  - `phototrap_safe_split_audit`
  - `phototrap_refactor_checkpoint`
- `codex exec` с явной инструкцией использовать только `phototrap_status` успешно выполнил MCP tool call к `phototrap-tools` и вернул статус проекта без shell-команд.
- `codex exec` с явной инструкцией использовать только `phototrap_safe_split_audit` успешно выполнил MCP tool call и вернул текущий split-аудит без shell-команд.
- `/home/japonamat/ai/lightrag/.venv/bin/python -m py_compile ...` для bootstrap/query-скриптов прошел успешно.
- `/home/japonamat/ai/lightrag/.venv/bin/python /home/japonamat/ai/lightrag/scripts/build_ai_index.py --dry-run` успешно вернул конфиг и список из `39` источников.
- `/home/japonamat/ai/lightrag/.venv/bin/python /home/japonamat/ai/lightrag/scripts/query_ai_index.py ...` сейчас корректно возвращает понятную ошибку о недоступном `ollama serve`, а не traceback.

## rollback

- Удалить каталог `/home/japonamat/ai/mcp/ai_control/`.
- Удалить этот recovery-файл.
- Удалить соответствующую запись из `~/ai/actions.log`, если нужен полностью ручной откат trail.

## relogin_or_reboot_requirement

Не требуется.

## next_steps

- Запустить `ollama serve`.
- Скачать модели `qwen2.5:1.5b` и `bge-m3:latest`.
- Собрать первый `ai_index`.
- Затем поднять индекс `Photo_Trap` и связать оба индекса с MCP tools.
