# PostgreSQL Context Store Bootstrap

## problem_statement

Нужно уйти от плана с `LightRAG` и вместо этого поднять контекстный слой для ассистента через `MCP + PostgreSQL`, не плодя новую СУБД и не перегружая `projects.db`, который до этого использовался как SQLite-индекс проектов.

## findings

- На машине уже есть рабочий system-level PostgreSQL `18.3`.
- Подключение к локальному серверу возможно по TCP `127.0.0.1` под пользователем `postgres`.
- Роль `japonamat` в PostgreSQL изначально отсутствовала.
- В системных базах обнаружен `collation version mismatch`:
  - `postgres`
  - `template1`
- Из-за этого обычный `CREATE DATABASE` через `template1` падает.
- Безопасный обходной путь для нового контекстного слоя сейчас: `CREATE DATABASE ... TEMPLATE template0`.

## exact_changes_made

- Создана PostgreSQL-роль `japonamat`.
- Создана база `ai_context` с владельцем `japonamat` через `TEMPLATE template0`.
- В `ai_context` создана минимальная схема:
  - `projects`
  - `documents`
  - `document_chunks`
  - `snapshots`
  - `ingestion_runs`
- Добавлено расширение `pg_trgm`.
- Добавлены индексы для `documents` и `snapshots`.
- Добавлены файлы bootstrap в `/home/japonamat/ai/postgres/`:
  - `context_schema.sql`
  - `sync_projects_from_sqlite.py`
  - `bootstrap_ai_context.sh`
  - `README.md`
- Выполнена первая синхронизация legacy-индекса из `/home/japonamat/ai/projects.db` в `ai_context.projects`.
- Добавлен первый MCP/core слой поверх `ai_context`:
  - `/home/japonamat/ai/mcp/context_tools/tools.py`
  - `/home/japonamat/ai/mcp/context_tools/cli.py`
  - `/home/japonamat/ai/mcp/context_tools/server.py`
  - `/home/japonamat/ai/mcp/context_tools/README.md`
- `context-tools` публикует инструменты:
  - `context_list_projects`
  - `context_get_project`
  - `context_list_snapshots`
  - `context_record_snapshot`
- `context-tools` зарегистрирован в `~/.codex/config.toml` как MCP server `context-tools`.

## verification_status

- `psql -h 127.0.0.1 -U japonamat -Atqc 'select current_user, current_database();' ai_context`
  - вернул `japonamat|ai_context`
- `psql -h 127.0.0.1 -U japonamat -Atqc 'select count(*) from projects;' ai_context`
  - вернул `12`
- `psql -h 127.0.0.1 -U japonamat -Atqc "select tablename from pg_tables where schemaname='public' order by tablename;" ai_context`
  - вернул все 5 таблиц схемы
- `python3 /home/japonamat/ai/postgres/sync_projects_from_sqlite.py`
  - успешно синхронизировал `12` project rows
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-projects`
  - успешно вернул список проектов из `ai_context.projects`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py context-get-project Photo_Trap`
  - успешно вернул строку проекта `Photo_Trap`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py context-record-snapshot ...`
  - успешно записал snapshots в `ai_context.snapshots`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py context-list-snapshots Photo_Trap --limit 3`
  - успешно вернул последние snapshots
- `codex exec` с явной инструкцией использовать только `context_list_snapshots`
  - успешно выполнил MCP tool call к `context-tools` и вернул, что для `Photo_Trap` уже есть `2` snapshots типа `safe_split_audit`

## rollback

- Удалить базу:
  - `psql -h 127.0.0.1 -U postgres -c "DROP DATABASE ai_context;"`
- При необходимости удалить роль:
  - `psql -h 127.0.0.1 -U postgres -c "DROP ROLE japonamat;"`
- Удалить bootstrap-файлы из `/home/japonamat/ai/postgres/`.

## relogin_or_reboot_requirement

Не требуется.

## next_steps

- Добавить MCP `context-tools` поверх `ai_context`.
- Перенести в Postgres не только `projects`, но и индексируемые документы:
  - `~/ai/recovery/*.md`
  - `~/ai/actions.log`
  - `Photo_Trap/.ai-recovery.md`
  - `Photo_Trap/docs/TODO.md`
- Добавить первые query-tools поверх `pg_trgm`.
