from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    get_project as get_project_core,
    kb_bootstrap_projection as kb_bootstrap_projection_core,
    kb_capture_project_bundle as kb_capture_project_bundle_core,
    kb_get_constraints as kb_get_constraints_core,
    kb_get_decisions as kb_get_decisions_core,
    kb_get_next_steps as kb_get_next_steps_core,
    kb_get_project_overview as kb_get_project_overview_core,
    kb_project_status as kb_project_status_core,
    kb_get_project_state as kb_get_project_state_core,
    kb_get_source_refs as kb_get_source_refs_core,
    kb_rebuild_project_projection as kb_rebuild_project_projection_core,
    kb_validate_projection as kb_validate_projection_core,
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


@server.tool(description="Capture the current source bundle for a project into ai_context.documents")
def kb_capture_project_bundle(project_name: str) -> dict:
    return kb_capture_project_bundle_core(project_name)


@server.tool(description="Build or update the knowledge-base projection for a project")
def kb_bootstrap_projection(project_name: str) -> dict:
    return kb_bootstrap_projection_core(project_name)


@server.tool(description="Rebuild the knowledge-base projection for a project from source files")
def kb_rebuild_project_projection(project_name: str) -> dict:
    return kb_rebuild_project_projection_core(project_name)


@server.tool(description="Get the current project overview from kb_projections")
def kb_get_project_overview(project_name: str) -> dict:
    return kb_get_project_overview_core(project_name)


@server.tool(description="Get compact project status aggregated from project row, projection, and recent snapshots")
def kb_project_status(project_name: str, snapshot_limit: int = 5) -> dict:
    return kb_project_status_core(project_name, snapshot_limit=snapshot_limit)


@server.tool(description="Get the current state summary and constraints from kb_projections")
def kb_get_project_state(project_name: str) -> dict:
    return kb_get_project_state_core(project_name)


@server.tool(description="Get next steps from kb_projections")
def kb_get_next_steps(project_name: str) -> dict:
    return kb_get_next_steps_core(project_name)


@server.tool(description="Get extracted project decisions from kb_projections")
def kb_get_decisions(project_name: str) -> dict:
    return kb_get_decisions_core(project_name)


@server.tool(description="Get extracted project constraints from kb_projections")
def kb_get_constraints(project_name: str) -> dict:
    return kb_get_constraints_core(project_name)


@server.tool(description="Get source refs used for the project projection")
def kb_get_source_refs(project_name: str) -> dict:
    return kb_get_source_refs_core(project_name)


@server.tool(description="Validate that the current project projection has the required fields")
def kb_validate_projection(project_name: str) -> dict:
    return kb_validate_projection_core(project_name)


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
