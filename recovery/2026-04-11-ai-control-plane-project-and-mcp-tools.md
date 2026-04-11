# ai-control-plane Project And MCP Tools

## problem_statement

Нужно было оформить текущую работу над `MCP + PostgreSQL + Codex launchers` как отдельный проект в БД и дать ему собственные MCP tools, чтобы эта инфраструктура была не только набором файлов в `~/ai`, а нормальным управляемым контекстом.

## findings

- `/home/japonamat/ai` уже является git-репозиторием.
- Remote: `git@github-auto:cmdrJaponamat/ai.git`.
- До изменения в `ai_context.projects` не было отдельного проекта для `~/ai` / MCP-инфраструктуры.
- Главные recovery-файлы по теме уже существовали в `~/ai/recovery/`, но не было project-root recovery `/home/japonamat/ai/.ai-recovery.md`.

## exact_changes_made

- Создан `/home/japonamat/ai/.ai-recovery.md` для проекта `ai-control-plane`.
- В `~/ai/PROJECT_CONTEXTS.md` добавлена запись:
  - `ai-control-plane`
  - path: `/home/japonamat/ai`
  - recovery: `/home/japonamat/ai/.ai-recovery.md`
- Через `~/ai/projects/register_project.sh` проект зарегистрирован в legacy `projects.db`.
- Через `~/ai/postgres/sync_projects_from_sqlite.py` проект синхронизирован в `ai_context.projects`.
- Через `context-tools` собрана `kb_projection` для `ai-control-plane`.
- Добавлен MCP слой `/home/japonamat/ai/mcp/ai_mcp_tools`:
  - `README.md`
  - `tools.py`
  - `cli.py`
  - `server.py`
- В `~/.codex/config.toml` добавлен MCP server:
  - `ai-mcp-tools`

## tools_added

- `ai_mcp_status`
- `ai_mcp_read_recovery`
- `ai_mcp_snapshot_audit`
- `ai_mcp_tooling_audit`
- `ai_mcp_read_file`
- `ai_mcp_search`

## verification_status

- `/home/japonamat/ai/projects/register_project.sh ai-control-plane ...`
  - успешно зарегистрировал проект.
- `python3 /home/japonamat/ai/postgres/sync_projects_from_sqlite.py`
  - синхронизировал `13` project rows.
- `psql ... select ... from projects where name='ai-control-plane'`
  - подтвердил наличие project row в `ai_context.projects`.
- `/home/japonamat/ai/mcp/.venv/bin/python3 -m py_compile .../ai_mcp_tools/*.py`
  - прошел успешно.
- `/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/ai_mcp_tools/cli.py ai-mcp-status`
  - успешно вернул git/MCP status.
- `/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-bootstrap-projection ai-control-plane`
  - успешно собрал projection.
- `ai-mcp-snapshot-audit`
  - записал snapshot `ai_mcp_snapshot_audit`.
- `ai-mcp-tooling-audit`
  - записал snapshot `ai_mcp_tooling_audit`.
- `codex mcp list`
  - показывает `ai-mcp-tools` как `enabled`.

## rollback

- Удалить `/home/japonamat/ai/mcp/ai_mcp_tools`.
- Удалить `/home/japonamat/ai/.ai-recovery.md`.
- Удалить запись `ai-control-plane` из `PROJECT_CONTEXTS.md`.
- Удалить или деактивировать строку проекта в `projects.db` и `ai_context.projects`.
- Убрать `[mcp_servers.ai-mcp-tools]` из `/home/japonamat/.codex/config.toml`.

## relogin_or_reboot_requirement

Не требуется.

Нужен перезапуск клиента `Codex`, чтобы новый MCP server был проброшен в runtime новой сессии.

## next_steps

- После перезапуска клиента проверить, виден ли `ai-mcp-tools` как runtime MCP namespace.
- Переделать `codex-ai-launcher-json` в MCP-first режим:
  - не инлайнить project recovery по умолчанию;
  - передавать выбранный project name;
  - использовать markdown recovery только как fallback.
