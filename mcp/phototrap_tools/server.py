from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    project_status as project_status_core,
    read_file as read_file_core,
    read_recovery as read_recovery_core,
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
