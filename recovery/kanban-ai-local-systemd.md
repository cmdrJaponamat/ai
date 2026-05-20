# Kanban AI Local Systemd Recovery

Date: 2026-05-20

## Problem

Kanban AI MVP needed live local monitoring instead of only manual MCP/shell runs.

## Changes Made

Installed user systemd units from:

```text
/home/admin-al/assistant/kanban/systemd/local/
```

to:

```text
/home/admin-al/.config/systemd/user/
```

Enabled and started timers:

```text
kanban-ai-local-monitor.timer
kanban-ai-weekly-review.timer
```

## Runtime Behavior

`kanban-ai-local-monitor.timer` runs every minute and triggers `kanban-ai-local-monitor.service`.

The service:

1. polls test board;
2. polls management board;
3. runs dispatcher without dry-run;
4. runs event executor with report output.

`kanban-ai-weekly-review.timer` runs Monday 12:00 MSK and triggers weekly-review apply workflow.

## Verification

Checked:

```bash
systemctl --user list-timers --all 'kanban-ai*' --no-pager
systemctl --user status kanban-ai-local-monitor.service --no-pager
```

Status: local monitor service completed successfully after enabling timers.

## Notes

The event executor is still report-only by implementation. It writes executor reports but does not mutate Kanban. Restricted apply is implemented in weekly-review and replan/apply-plan workflows.

Dispatcher was updated so observe/no-op events remain decisions but are not written into `queue/actions`.

## Rollback

```bash
systemctl --user disable --now kanban-ai-local-monitor.timer
systemctl --user disable --now kanban-ai-weekly-review.timer
rm -f ~/.config/systemd/user/kanban-ai-local-monitor.service
rm -f ~/.config/systemd/user/kanban-ai-local-monitor.timer
rm -f ~/.config/systemd/user/kanban-ai-weekly-review.service
rm -f ~/.config/systemd/user/kanban-ai-weekly-review.timer
systemctl --user daemon-reload
```

## Relogin/Reboot

Not required.
