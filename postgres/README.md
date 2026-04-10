# PostgreSQL Context Store

Здесь лежит воспроизводимый bootstrap для контекстного слоя ассистента поверх локального PostgreSQL.

Текущий дизайн:

- `projects.db` остается legacy-индексом проектов
- `ai_context` в PostgreSQL становится новой базой для:
  - проектов
  - документов
  - чанков
  - snapshots
  - ingestion runs

## Текущая база

- host: `127.0.0.1`
- db: `ai_context`
- user: `japonamat`

## Быстрые команды

Проверка подключения:

```bash
psql -h 127.0.0.1 -U japonamat -Atqc 'select current_user, current_database();' ai_context
```

Накатить схему:

```bash
psql -h 127.0.0.1 -U japonamat -f /home/japonamat/ai/postgres/context_schema.sql ai_context
```

Полный bootstrap базы и роли:

```bash
/home/japonamat/ai/postgres/bootstrap_ai_context.sh
```

Синхронизировать проекты из legacy `projects.db`:

```bash
python3 /home/japonamat/ai/postgres/sync_projects_from_sqlite.py
```

## Замечание по серверу

При bootstrap обнаружен `collation version mismatch` в системных базах `postgres/template1`.

Практически это означает:

- стандартный `CREATE DATABASE` через `template1` ломается
- пока безопасный обходной путь: создавать новые базы через `TEMPLATE template0`

Это не блокирует текущий контекстный слой, но системный PostgreSQL потом стоит отдельно привести в порядок.
