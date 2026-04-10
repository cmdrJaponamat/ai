from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path


SQLITE_DB = Path("/home/japonamat/ai/projects.db")
PG_DSN = ["psql", "-h", "127.0.0.1", "-U", "japonamat", "ai_context"]


def load_projects() -> list[tuple[str, str, str, str, int]]:
    with sqlite3.connect(SQLITE_DB) as conn:
        rows = conn.execute(
            """
            select name, path, repo_root, recovery_file, active
            from projects
            order by id
            """
        ).fetchall()
    return rows


def sql_escape(value: str) -> str:
    return value.replace("'", "''")


def build_sql(rows: list[tuple[str, str, str, str, int]]) -> str:
    statements = []
    for name, path, repo_root, recovery_file, active in rows:
        statements.append(
            f"""
            INSERT INTO projects (name, path, repo_root, recovery_file, active, source, created_at, updated_at)
            VALUES (
                '{sql_escape(name)}',
                '{sql_escape(path)}',
                '{sql_escape(repo_root)}',
                '{sql_escape(recovery_file)}',
                {'TRUE' if active else 'FALSE'},
                'sqlite_migration',
                now(),
                now()
            )
            ON CONFLICT(path) DO UPDATE SET
                name = EXCLUDED.name,
                repo_root = EXCLUDED.repo_root,
                recovery_file = EXCLUDED.recovery_file,
                active = EXCLUDED.active,
                updated_at = now();
            """
        )
    return "\n".join(statements)


def main() -> int:
    rows = load_projects()
    if not rows:
        print("No projects found in SQLite source.")
        return 0

    sql = build_sql(rows)
    completed = subprocess.run(
        PG_DSN,
        input=sql,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "psql sync failed")

    print(f"Synced {len(rows)} project rows into ai_context.projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
