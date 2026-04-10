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
- Затем схема расширена таблицей `kb_projections` для компактных project projection:
  - `overview`
  - `state_summary`
  - `next_steps`
  - `decisions`
  - `constraints`
  - `source_refs`
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
- `context-tools` затем расширен kb-инструментами:
  - `kb_capture_project_bundle`
  - `kb_bootstrap_projection`
  - `kb_rebuild_project_projection`
  - `kb_get_project_overview`
  - `kb_get_project_state`
  - `kb_get_next_steps`
  - `kb_get_decisions`
  - `kb_get_constraints`
  - `kb_get_source_refs`
  - `kb_validate_projection`
- `context-tools` зарегистрирован в `~/.codex/config.toml` как MCP server `context-tools`.
- Для `Photo_Trap` собран первый `kb_projection` из:
  - `.ai-recovery.md`
  - `docs/TODO.md`
  - `docs/ARCHITECTURE.md`
  - `README.md`
- Исправлено чтение `kb_projections`: вместо разбора `psql -AtF "\\t"` по табам теперь используется `row_to_json(...)`, чтобы многострочные поля и JSON-массивы не ломали загрузку projection.
- `context-tools` переведен с shell-вызовов `psql` на `psycopg`-адаптер, частично заимствованный по подходу из `CodexKnowledgeHelper`:
  - env-driven `DBSettings`
  - `DBRepository`
  - прямые параметризованные SQL-запросы вместо shell transport

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
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-bootstrap-projection Photo_Trap`
  - успешно собрал `kb_projection` для `Photo_Trap`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-project-overview Photo_Trap`
  - успешно вернул `overview`, `source_refs` и `updated_at`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-project-state Photo_Trap`
  - успешно вернул `state_summary` и `constraints`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-next-steps Photo_Trap`
  - успешно вернул extracted `next_steps`
- `python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-validate-projection Photo_Trap`
  - вернул `valid: true`
- `psql -h 127.0.0.1 -U japonamat -d ai_context -c 'select ... from kb_projections;'`
  - подтвердил, что projection-row реально существует в базе
- `/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-get-project-overview Photo_Trap`
  - успешно отработал уже через `psycopg`
- `/home/japonamat/ai/mcp/.venv/bin/python3 /home/japonamat/ai/mcp/context_tools/cli.py kb-validate-projection Photo_Trap`
  - успешно отработал уже через `psycopg`
- `codex exec` с явной инструкцией использовать только `context_list_snapshots`
  - успешно выполнил MCP tool call к `context-tools` и вернул, что для `Photo_Trap` уже есть `2` snapshots типа `safe_split_audit`
- Повторная `codex exec` проверка для `kb_get_project_overview`
  - не завершилась из-за client usage limit
  - это внешний лимит клиента, а не ошибка MCP server или SQL-слоя

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
- Автоматически писать в `snapshots` результаты:
  - `phototrap_safe_split_audit`
  - `phototrap_refactor_checkpoint`
  - `phototrap_recovery_sync_audit`
  - `phototrap_module_seam_check`
- Добавить query-tools поверх `pg_trgm` и `documents`.
- Сжать extraction-логику для `next_steps` и `state_summary`, чтобы в projection не попадали лишние markdown-заголовки.
- При желании потом вынести этот DB-слой в общий `ai/mcp/db_runtime`, чтобы его могли переиспользовать и другие MCP servers.
