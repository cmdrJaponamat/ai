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

## verification_status

- `python3 /home/japonamat/ai/mcp/ai_control/cli.py list-projects` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py read-project-recovery Photo_Trap` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py search-recovery Photo_Trap --limit 5` отработал успешно.
- `python3 /home/japonamat/ai/mcp/ai_control/cli.py search-actions-log github-auto --limit 5` отработал успешно.

## rollback

- Удалить каталог `/home/japonamat/ai/mcp/ai_control/`.
- Удалить этот recovery-файл.
- Удалить соответствующую запись из `~/ai/actions.log`, если нужен полностью ручной откат trail.

## relogin_or_reboot_requirement

Не требуется.

## next_steps

- Поверх текущего core добавить настоящий MCP transport.
- После этого поднять узкий `LightRAG`-индекс для `~/ai`.
- Затем сделать отдельный `phototrap-tools` и индекс `Photo_Trap`.
