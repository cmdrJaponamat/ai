from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    get_project as get_project_core,
    list_projects as list_projects_core,
    list_snapshots as list_snapshots_core,
    record_snapshot as record_snapshot_core,
)


server = FastMCP(
    name="context-tools",
    instructions=(
        "Access the PostgreSQL context store ai_context. "
        "Use these tools for project registry lookup and project snapshot persistence."
    ),
)


@server.tool(description="List projects stored in ai_context.projects")
def context_list_projects() -> list[dict]:
    return list_projects_core()


@server.tool(description="Get one project by name from ai_context.projects")
def context_get_project(project_name: str) -> dict:
    return get_project_core(project_name)


@server.tool(description="List recent snapshots for a project from ai_context.snapshots")
def context_list_snapshots(project_name: str, snapshot_type: str | None = None, limit: int = 10) -> list[dict]:
    return list_snapshots_core(project_name, snapshot_type=snapshot_type, limit=limit)


@server.tool(description="Record a snapshot payload for a project into ai_context.snapshots")
def context_record_snapshot(
    project_name: str,
    snapshot_type: str,
    payload: dict,
    title: str | None = None,
) -> dict:
    return record_snapshot_core(project_name, snapshot_type, payload, title=title)


if __name__ == "__main__":
    server.run("stdio")
