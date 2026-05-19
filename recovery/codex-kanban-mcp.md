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

Incomplete:

- `codex exec` smoke check started but did not produce final output in the allotted wait. No related process remained running after the check.

## Rollback

```bash
codex mcp remove kanban-ai
cp /home/admin-al/.codex/config.toml.bak-kanban-mcp-YYYYMMDD-HHMMSS /home/admin-al/.codex/config.toml
```

## Restart / Relogin

No relogin, reboot, or service restart required.
