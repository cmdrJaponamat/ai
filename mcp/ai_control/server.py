from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    append_actions_log as append_actions_log_core,
    list_projects as list_projects_core,
    read_project_recovery as read_project_recovery_core,
    search_actions_log as search_actions_log_core,
    search_recovery_notes,
)


server = FastMCP(
    name="ai-control",
    instructions=(
        "Access the user's ~/ai control plane. "
        "Use these tools for project registry lookup, recovery reading, "
        "basic recovery search, and actions log updates."
    ),
)


@server.tool(description="List projects registered in ~/ai/PROJECT_CONTEXTS.md")
def list_projects() -> list[dict[str, str]]:
    return [
        {
            "name": entry.name,
            "path": str(entry.path),
            "recovery": str(entry.recovery),
        }
        for entry in list_projects_core()
    ]


@server.tool(description="Read the .ai-recovery.md content for a registered project by name")
def read_project_recovery(project_name: str) -> str:
    return read_project_recovery_core(project_name)


@server.tool(description="Search markdown files in ~/ai/recovery for a text query")
def search_recovery(query: str, limit: int = 10) -> list[dict[str, str | int]]:
    return [
        {
            "path": str(hit.path),
            "line_number": hit.line_number,
            "line": hit.line,
        }
        for hit in search_recovery_notes(query, limit=limit)
    ]


@server.tool(description="Search ~/ai/actions.log for a text query")
def search_actions_log(query: str, limit: int = 10) -> list[dict[str, str | int]]:
    return [
        {
            "line_number": hit.line_number,
            "line": hit.line,
        }
        for hit in search_actions_log_core(query, limit=limit)
    ]


@server.tool(description="Append a structured line to ~/ai/actions.log")
def append_actions_log(
    what_changed: str,
    why_changed: str,
    verification_status: str,
    rollback_strategy_or_note: str = "not specified",
    relogin_or_reboot_requirement: str = "not required",
) -> str:
    return append_actions_log_core(
        what_changed=what_changed,
        why_changed=why_changed,
        verification_status=verification_status,
        rollback_strategy_or_note=rollback_strategy_or_note,
        relogin_or_reboot_requirement=relogin_or_reboot_requirement,
    )


if __name__ == "__main__":
    server.run("stdio")
