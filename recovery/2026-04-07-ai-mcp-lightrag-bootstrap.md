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

## rollback

- Удалить каталог `/home/japonamat/ai/mcp/ai_control/`.
- Удалить этот recovery-файл.
- Удалить соответствующую запись из `~/ai/actions.log`, если нужен полностью ручной откат trail.

## relogin_or_reboot_requirement

Не требуется.

## next_steps

- После этого поднять узкий `LightRAG`-индекс для `~/ai`.
- Затем сделать отдельный `phototrap-tools` и индекс `Photo_Trap`.
