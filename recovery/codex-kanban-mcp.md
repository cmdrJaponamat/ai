# Codex Kanban MCP Recovery

Date: 2026-05-19

## Problem Statement

Codex needs to work with existing Kanban AI tools through MCP instead of directly calling internal scripts or PLANKA APIs.

## Changes Made

- Added stdio MCP server:
  - `/home/admin-al/assistant/mcp/kanban_ai_mcp.py`
- Registered global Codex MCP server:
  - `kanban-ai`
- Codex config changed:
  - `/home/admin-al/.codex/config.toml`
- Added startup timeout:
  - `startup_timeout_sec = 60`
- Adjusted MCP initialize handshake:
  - returns the client-requested `protocolVersion`
  - declares `tools.listChanged = false`
- Later removed the global `kanban-ai` MCP registration because Codex CLI 0.131.0 still timed out on stdio startup and blocked session startup.
- Cloned and inspected working MCP examples from:
  - `git@github.com:cmdrJaponamat/ai.git`
- Found that the working examples use the official Python MCP SDK:
  - `mcp==1.27.0`
  - `mcp.server.fastmcp.FastMCP`
- Created local MCP venv:
  - `/home/admin-al/assistant/mcp/.venv`
- Added FastMCP wrapper:
  - `/home/admin-al/assistant/mcp/kanban_ai_fastmcp.py`
- Re-registered global Codex MCP server `kanban-ai` through venv Python and `kanban_ai_fastmcp.py`.
- A timestamped backup of the Codex config was created before registration:
  - `/home/admin-al/.codex/config.toml.bak-kanban-mcp-*`

## Exposed MCP Tools

- `kanban_board_summary`
- `kanban_cards`
- `kanban_project_metadata`
- `kanban_build_project_context`
- `kanban_run_handler`
- `kanban_run_dispatcher`
- `kanban_run_executor`

## Safety Notes

- No raw PLANKA mutation API is exposed through MCP.
- Executor remains dry-run.
- PLANKA credentials are not stored in Codex MCP config; the server reads the existing env file.

## Verification

Passed:

- Direct MCP `initialize` request.
- Direct MCP `initialize` request with `protocolVersion: 2025-06-18` returned the same protocol version in about 0.1 seconds.
- Direct MCP `tools/list` request.
- Direct MCP `tools/call` for `kanban_board_summary`.
- `codex mcp list` shows `kanban-ai` enabled.
- `codex mcp get kanban-ai` shows stdio command path and `startup_timeout_sec: 60`.

Later diagnostic result:

- Direct MCP protocol tests still pass.
- TUI/PTTY diagnostics show Codex starts the MCP process, but sends no bytes to the server stdin before timing out.
- The same behavior remains after explicit `/usr/bin/python3`, explicit `cwd`, `startup_timeout_sec = 60`, and `--disable apps`.
- `npm view @openai/codex version` showed `0.131.0`, same as installed.

Current state:

- `kanban-ai` is registered in `~/.codex/config.toml`.
- `codex mcp list` shows `kanban-ai` enabled.
- Active command:
  - `/home/admin-al/assistant/mcp/.venv/bin/python3 /home/admin-al/assistant/mcp/kanban_ai_fastmcp.py`
- The legacy manual stdio server is kept in `/home/admin-al/assistant/mcp/kanban_ai_mcp.py` for diagnostics only.

FastMCP verification:

- `/home/admin-al/assistant/mcp/.venv/bin/python3 -m py_compile /home/admin-al/assistant/mcp/kanban_ai_fastmcp.py /home/admin-al/assistant/mcp/kanban_ai_mcp.py` passed.
- `codex mcp add kanban-ai -- /home/admin-al/assistant/mcp/.venv/bin/python3 /home/admin-al/assistant/mcp/kanban_ai_fastmcp.py` passed.
- `codex mcp list` and `codex mcp get kanban-ai` show the FastMCP server enabled.
- `codex exec --dangerously-bypass-approvals-and-sandbox` successfully called `kanban-ai/kanban_cards` for board `test`.
- `codex exec` without bypass starts the MCP tool but cancels it with `user cancelled MCP tool call`; this is an approval-policy issue in non-interactive execution, not an MCP startup timeout.

## Rollback

```bash
codex mcp remove kanban-ai
```

The local venv can be removed if MCP is no longer needed:

```bash
rm -rf /home/admin-al/assistant/mcp/.venv
```

## Restart / Relogin

No relogin, reboot, or service restart required.
