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

- `kanban-ai` is not registered in `~/.codex/config.toml`.
- `codex mcp list` reports no MCP servers configured.
- The MCP server file is kept in `/home/admin-al/assistant/mcp/kanban_ai_mcp.py` for future retest or HTTP MCP service conversion.

## Rollback

```bash
cp /home/admin-al/.codex/config.toml.bak-kanban-mcp-YYYYMMDD-HHMMSS /home/admin-al/.codex/config.toml
```

## Restart / Relogin

No relogin, reboot, or service restart required.
