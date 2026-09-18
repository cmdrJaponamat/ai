from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys


CONTEXT_TOOLS_DIR = Path("/home/japonamat/ai/mcp/context_tools")
if str(CONTEXT_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(CONTEXT_TOOLS_DIR))

from db_runtime import DBRepository


PROJECT_NAME = "ai-control-plane"
PROJECT_ROOT = Path("/home/japonamat/ai")
RECOVERY_FILE = PROJECT_ROOT / ".ai-recovery.md"
REPOSITORY = DBRepository()


def _run_command(command: list[str], cwd: Path = PROJECT_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _normalize_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _project_row() -> dict | None:
    return REPOSITORY.fetch_one(
        """
        select id, name, path, repo_root, recovery_file, active
        from projects
        where lower(name) = lower(%s)
        limit 1
        """,
        (PROJECT_NAME,),
    )


def _record_snapshot(snapshot_type: str, payload: dict, title: str | None = None) -> dict | None:
    project = _project_row()
    if project is None:
        return None
    row = REPOSITORY.execute_returning_one(
        """
        insert into snapshots (project_id, snapshot_type, title, payload)
        values (%s, %s, %s, %s::jsonb)
        returning id, created_at::text as created_at
        """,
        (
            project["id"],
            snapshot_type,
            title,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "snapshot_type": snapshot_type,
        "created_at": row["created_at"],
    }


def read_recovery() -> str:
    return RECOVERY_FILE.read_text(encoding="utf-8")


def read_file(relative_path: str) -> str:
    target = (PROJECT_ROOT / relative_path).resolve()
    try:
        target.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path escapes project root: {relative_path}") from exc
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {relative_path}")
    return target.read_text(encoding="utf-8")


def search(query: str, limit: int = 10) -> list[dict]:
    completed = _run_command(
        [
            "rg",
            "-n",
            "--no-heading",
            "--color",
            "never",
            "--glob",
            "!.git",
            "--glob",
            "!mcp/.venv",
            "--glob",
            "!lightrag/.venv",
            query,
            str(PROJECT_ROOT),
        ]
    )
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr.strip() or "rg search failed")

    hits: list[dict] = []
    for raw_line in completed.stdout.splitlines():
        parts = raw_line.split(":", 2)
        if len(parts) != 3:
            continue
        path_text, line_number_text, line = parts
        hits.append(
            {
                "path": _normalize_path(Path(path_text)),
                "line_number": int(line_number_text),
                "line": line.strip(),
            }
        )
        if len(hits) >= limit:
            break
    return hits


def status() -> dict:
    git_status = _run_command(["git", "status", "--short", "--branch"]).stdout.strip()
    git_log = _run_command(["git", "log", "--oneline", "-n", "8"]).stdout.strip().splitlines()
    mcp_list = _run_command(["codex", "mcp", "list"]).stdout.strip()
    project = _project_row()
    return {
        "project_name": PROJECT_NAME,
        "project_root": str(PROJECT_ROOT),
        "registered_in_ai_context": project is not None,
        "git_status": git_status,
        "recent_commits": git_log,
        "mcp_list": mcp_list,
    }


def tooling_audit() -> dict:
    server_dirs = ["ai_control", "context_tools", "phototrap_tools", "ai_mcp_tools"]
    dirs = []
    for name in server_dirs:
        path = PROJECT_ROOT / "mcp" / name
        dirs.append(
            {
                "name": name,
                "exists": path.is_dir(),
                "server_py": (path / "server.py").is_file(),
                "tools_py": (path / "tools.py").is_file(),
                "cli_py": (path / "cli.py").is_file(),
                "readme": (path / "README.md").is_file(),
            }
        )
    result = {
        "project_root": str(PROJECT_ROOT),
        "requirements_exists": (PROJECT_ROOT / "mcp" / "requirements.txt").is_file(),
        "venv_exists": (PROJECT_ROOT / "mcp" / ".venv").is_dir(),
        "servers": dirs,
    }
    snapshot = _record_snapshot("ai_mcp_tooling_audit", result, title="AI MCP tooling audit")
    if snapshot is not None:
        result["snapshot_recorded"] = snapshot
    return result


def snapshot_audit() -> dict:
    project = _project_row()
    row = REPOSITORY.fetch_one(
        """
        select
            (select count(*) from projects)::int as project_count,
            (select count(*) from documents)::int as document_count,
            (select count(*) from snapshots)::int as snapshot_count,
            (select count(*) from kb_projections)::int as projection_count
        """
    )
    project_snapshots = []
    if project is not None:
        project_snapshots = REPOSITORY.fetch_all(
            """
            select snapshot_type, count(*)::int as count
            from snapshots
            where project_id = %s
            group by snapshot_type
            order by snapshot_type
            """,
            (project["id"],),
        )
    result = {
        "project_name": PROJECT_NAME,
        "registered_in_ai_context": project is not None,
        "database_counts": row or {},
        "project_snapshot_counts": project_snapshots,
    }
    snapshot = _record_snapshot("ai_mcp_snapshot_audit", result, title="AI MCP snapshot audit")
    if snapshot is not None:
        result["snapshot_recorded"] = snapshot
    return result

