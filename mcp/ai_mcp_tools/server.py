from __future__ import annotations

from pathlib import Path
import sys

from mcp.server.fastmcp import FastMCP


CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from tools import (
    read_file as read_file_core,
    read_recovery as read_recovery_core,
    search as search_core,
    snapshot_audit as snapshot_audit_core,
    status as status_core,
    tooling_audit as tooling_audit_core,
)


server = FastMCP(
    name="ai-mcp-tools",
    instructions=(
        "Access the ai-control-plane project through stable tools. "
        "Use these tools to inspect MCP/PostgreSQL infrastructure and recovery state."
    ),
)


@server.tool(description="Return ai-control-plane git, MCP, and registration status")
def ai_mcp_status() -> dict:
    return status_core()


@server.tool(description="Read /home/japonamat/ai/.ai-recovery.md")
def ai_mcp_read_recovery() -> str:
    return read_recovery_core()


@server.tool(description="Audit ai_context project/document/snapshot/projection counts and persist a snapshot")
def ai_mcp_snapshot_audit() -> dict:
    return snapshot_audit_core()


@server.tool(description="Audit MCP server directories and key files and persist a snapshot")
def ai_mcp_tooling_audit() -> dict:
    return tooling_audit_core()


@server.tool(description="Read a file inside /home/japonamat/ai by relative path")
def ai_mcp_read_file(relative_path: str) -> str:
    return read_file_core(relative_path)


@server.tool(description="Search /home/japonamat/ai for a text query")
def ai_mcp_search(query: str, limit: int = 10) -> list[dict]:
    return search_core(query, limit=limit)


if __name__ == "__main__":
    server.run("stdio")

