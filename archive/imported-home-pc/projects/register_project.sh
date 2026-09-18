#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 <name> <project_path> <recovery_file> [remote_url]" >&2
  exit 1
fi

NAME="$1"
PROJECT_PATH="$(realpath "$2")"
RECOVERY_FILE="$(realpath "$3")"
REMOTE_URL="${4:-}"

DB="$HOME/ai/projects.db"

if [[ ! -f "$DB" ]]; then
  echo "projects.db not found: $DB" >&2
  exit 1
fi

if [[ ! -d "$PROJECT_PATH" ]]; then
  echo "project path not found: $PROJECT_PATH" >&2
  exit 1
fi

if [[ ! -f "$RECOVERY_FILE" ]]; then
  echo "recovery file not found: $RECOVERY_FILE" >&2
  exit 1
fi

sqlite3 "$DB" <<SQL
INSERT INTO projects (name, path, repo_root, recovery_file, active, created_at, updated_at)
VALUES (
  '$NAME',
  '$PROJECT_PATH',
  '$PROJECT_PATH',
  '$RECOVERY_FILE',
  1,
  datetime('now'),
  datetime('now')
)
ON CONFLICT(path) DO UPDATE SET
  name=excluded.name,
  repo_root=excluded.repo_root,
  recovery_file=excluded.recovery_file,
  active=excluded.active,
  updated_at=datetime('now');
SQL

if [[ -n "$REMOTE_URL" ]]; then
  sqlite3 "$DB" <<SQL
INSERT INTO project_remotes (project_id, remote_name, remote_url, remote_kind, owner_ok)
SELECT
  id,
  'origin',
  '$REMOTE_URL',
  CASE
    WHEN '$REMOTE_URL' LIKE 'git@%' THEN 'ssh'
    WHEN '$REMOTE_URL' LIKE 'https://%' THEN 'https'
    ELSE 'unknown'
  END,
  CASE
    WHEN '$REMOTE_URL' LIKE '%cmdrJaponamat%' THEN 1
    ELSE 0
  END
FROM projects
WHERE path = '$PROJECT_PATH'
ON CONFLICT(project_id, remote_name, remote_url, remote_kind) DO NOTHING;
SQL
fi

echo "Registered project: $NAME"
