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

## verification_status

- `psql -h 127.0.0.1 -U japonamat -Atqc 'select current_user, current_database();' ai_context`
  - вернул `japonamat|ai_context`
- `psql -h 127.0.0.1 -U japonamat -Atqc 'select count(*) from projects;' ai_context`
  - вернул `12`
- `psql -h 127.0.0.1 -U japonamat -Atqc "select tablename from pg_tables where schemaname='public' order by tablename;" ai_context`
  - вернул все 5 таблиц схемы
- `python3 /home/japonamat/ai/postgres/sync_projects_from_sqlite.py`
  - успешно синхронизировал `12` project rows

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
