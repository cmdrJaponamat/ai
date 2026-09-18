from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    module_seam_check as module_seam_check_core,
    project_status as project_status_core,
    read_file as read_file_core,
    read_recovery as read_recovery_core,
    recovery_sync_audit as recovery_sync_audit_core,
    refactor_checkpoint as refactor_checkpoint_core,
    safe_split_audit as safe_split_audit_core,
    search_code as search_code_core,
)


server = FastMCP(
    name="phototrap-tools",
    instructions=(
        "Access the Photo_Trap project through stable project-level tools. "
        "Use these tools for project recovery, git status, code search, and file reads."
    ),
)


@server.tool(description="Return a short git status summary for the Photo_Trap project")
def phototrap_status() -> dict[str, str]:
    return project_status_core()


@server.tool(description="Read the Photo_Trap .ai-recovery.md file")
def phototrap_read_recovery() -> str:
    return read_recovery_core()


@server.tool(description="Audit large Kotlin files and show which ones exceed the current split limit")
def phototrap_safe_split_audit(top_n: int = 15, line_limit: int = 700) -> dict:
    return safe_split_audit_core(top_n=top_n, line_limit=line_limit)


@server.tool(description="Run a refactor checkpoint: git status, large Kotlin files, limit audit, and assembleDebug")
def phototrap_refactor_checkpoint(top_n: int = 10, line_limit: int = 700) -> dict:
    return refactor_checkpoint_core(top_n=top_n, line_limit=line_limit)


@server.tool(description="Check which recent architecture/refactor commits are not yet reflected in .ai-recovery.md and docs/TODO.md")
def phototrap_recovery_sync_audit(limit: int = 20) -> dict:
    return recovery_sync_audit_core(limit=limit)


@server.tool(description="Check which internal Kotlin dependencies already go through policy/repository/controller seams and where hard concrete dependencies remain")
def phototrap_module_seam_check(top_n: int = 12) -> dict:
    return module_seam_check_core(top_n=top_n)


@server.tool(description="Read a file inside the Photo_Trap project by relative path")
def phototrap_read_file(relative_path: str) -> str:
    return read_file_core(relative_path)


@server.tool(description="Search the Photo_Trap project for a text query")
def phototrap_search_code(query: str, limit: int = 10) -> list[dict[str, str | int]]:
    return [
        {
            "path": str(hit.path),
            "line_number": hit.line_number,
            "line": hit.line,
        }
        for hit in search_code_core(query, limit=limit)
    ]


if __name__ == "__main__":
    server.run("stdio")
