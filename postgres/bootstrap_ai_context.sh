#!/usr/bin/env bash
set -euo pipefail

PGHOST="${PGHOST:-127.0.0.1}"
PGSUPERUSER="${PGSUPERUSER:-postgres}"
APP_USER="${APP_USER:-japonamat}"
APP_DB="${APP_DB:-ai_context}"

psql -h "$PGHOST" -U "$PGSUPERUSER" -v ON_ERROR_STOP=1 postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$APP_USER') THEN
    EXECUTE format('CREATE ROLE %I LOGIN', '$APP_USER');
  END IF;
END
\$\$;
SQL

if ! psql -h "$PGHOST" -U "$PGSUPERUSER" -Atqc "select 1 from pg_database where datname = '$APP_DB';" postgres | grep -q 1; then
  psql -h "$PGHOST" -U "$PGSUPERUSER" -v ON_ERROR_STOP=1 postgres \
    -c "CREATE DATABASE $APP_DB OWNER $APP_USER TEMPLATE template0;"
fi

psql -h "$PGHOST" -U "$PGSUPERUSER" -v ON_ERROR_STOP=1 "$APP_DB" <<SQL
ALTER DATABASE $APP_DB OWNER TO $APP_USER;
GRANT ALL PRIVILEGES ON DATABASE $APP_DB TO $APP_USER;
SQL

psql -h "$PGHOST" -U "$APP_USER" -f /home/japonamat/ai/postgres/context_schema.sql "$APP_DB"

echo "Bootstrapped PostgreSQL context store: db=$APP_DB user=$APP_USER host=$PGHOST"
