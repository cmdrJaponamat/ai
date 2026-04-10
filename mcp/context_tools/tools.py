from __future__ import annotations

from pathlib import Path
import json
import subprocess


PG_DSN = ["psql", "-h", "127.0.0.1", "-U", "japonamat", "ai_context"]


def _run_sql(sql: str) -> str:
    completed = subprocess.run(
        PG_DSN + ["-AtF", "\t", "-c", sql],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "psql query failed")
    return completed.stdout.strip()


def _first_data_line(output: str) -> str:
    for line in output.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.startswith(("INSERT ", "UPDATE ", "DELETE ")):
            continue
        return normalized
    return ""


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


def list_projects() -> list[dict[str, str | int | bool]]:
    output = _run_sql(
        """
        select id, name, path, repo_root, coalesce(recovery_file, ''), active
        from projects
        order by id;
        """
    )
    rows = []
    for line in output.splitlines():
        if not line:
            continue
        project_id, name, path, repo_root, recovery_file, active = line.split("\t", 5)
        rows.append(
            {
                "id": int(project_id),
                "name": name,
                "path": path,
                "repo_root": repo_root,
                "recovery_file": recovery_file,
                "active": active == "t",
            }
        )
    return rows


def get_project(project_name: str) -> dict[str, str | int | bool]:
    escaped = _sql_escape(project_name)
    output = _run_sql(
        f"""
        select id, name, path, repo_root, coalesce(recovery_file, ''), active
        from projects
        where lower(name) = lower('{escaped}')
        limit 1;
        """
    )
    if not output:
        raise ValueError(f"Project not found in ai_context: {project_name}")
    project_id, name, path, repo_root, recovery_file, active = output.split("\t", 5)
    return {
        "id": int(project_id),
        "name": name,
        "path": path,
        "repo_root": repo_root,
        "recovery_file": recovery_file,
        "active": active == "t",
    }


def list_snapshots(project_name: str, snapshot_type: str | None = None, limit: int = 10) -> list[dict]:
    project = get_project(project_name)
    snapshot_filter = ""
    if snapshot_type:
        snapshot_filter = f"and snapshot_type = '{_sql_escape(snapshot_type)}'"

    output = _run_sql(
        f"""
        select id, snapshot_type, coalesce(title, ''), payload::text, created_at::text
        from snapshots
        where project_id = {project["id"]}
          {snapshot_filter}
        order by id desc
        limit {int(limit)};
        """
    )

    rows = []
    for line in output.splitlines():
        if not line:
            continue
        snapshot_id, kind, title, payload_text, created_at = line.split("\t", 4)
        rows.append(
            {
                "id": int(snapshot_id),
                "project_name": project["name"],
                "snapshot_type": kind,
                "title": title,
                "payload": json.loads(payload_text),
                "created_at": created_at,
            }
        )
    return rows


def record_snapshot(
    project_name: str,
    snapshot_type: str,
    payload: dict,
    title: str | None = None,
) -> dict[str, str | int]:
    project = get_project(project_name)
    payload_json = json.dumps(payload, ensure_ascii=False)
    title_sql = "NULL" if title is None else f"'{_sql_escape(title)}'"

    snapshot_output = _run_sql(
        f"""
        insert into snapshots (project_id, snapshot_type, title, payload)
        values (
            {project["id"]},
            '{_sql_escape(snapshot_type)}',
            {title_sql},
            '{_sql_escape(payload_json)}'::jsonb
        )
        returning id;
        """
    )
    snapshot_id = _first_data_line(snapshot_output)
    if not snapshot_id:
        raise RuntimeError("Snapshot insert returned no id")
    return {
        "id": int(snapshot_id),
        "project_name": str(project["name"]),
        "snapshot_type": snapshot_type,
    }
