# Niri X11 Context

Date: 2026-03-13
User: japonamat
Host context: /home/japonamat

## Working Rules

- Log all system-level actions into files under `~/ai/`.
- Commit every change under `.config` immediately after each discrete action.
- Create or update recovery/context files in `~/ai/` after every completed task or system change.

## Problem

In the current `niri` session, X11 clients cannot open `DISPLAY=:1`.

Observed failures:
- `xdpyinfo`: `unable to open display ":1"`
- `xset`: `unable to open display ":1"`
- `xprop`: `unable to open display ':1'`
- `plantuml -version`: Java AWT error connecting to X11

## What Was Verified

- Session type is Wayland:
  - `XDG_SESSION_TYPE=wayland`
  - `XDG_CURRENT_DESKTOP=niri`
  - `DISPLAY=:1`
  - `WAYLAND_DISPLAY=wayland-1`
- Xwayland is running:
  - `Xwayland :1`
  - socket exists: `/tmp/.X11-unix/X1`
- No X11 auth is available to the user session:
  - `XAUTHORITY` unset
  - `~/.Xauthority` does not exist
- This is not a PlantUML-specific issue. Direct X11 tools fail too.

## Niri-Specific Finding

Installed version:
- `niri 25.11-1`
- `xwayland-satellite 0.8.1-1`

Important detail:
- `niri` 25.11 already integrates Xwayland via `xwayland-satellite`
- `niri` logs showed:
  - `listening on X11 socket: :1`
  - `spawning xwayland-satellite`

Conclusion:
- X11 should be managed by `niri` itself
- old manual environment glue is likely interfering or at least unnecessary

## Changes Already Made

1. Removed manual environment import from:
   `/home/japonamat/.config/niri/autostart.sh`

Removed line:
```sh
dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP=niri NIRI_SOCKET
```

2. Disabled the user service:
```sh
systemctl --user disable xwayland-satellite.service
```

Reason:
- avoid a second/manual Xwayland control path
- let `niri` own X11 startup

## Expected Next Step

These changes need a full logout/login of the `niri` session.

After logging back into `niri`, run:
```bash
xdpyinfo | head
xprop -root
plantuml -version
```

## Expected Good Result

- `xdpyinfo` prints X server info
- `xprop -root` works
- `plantuml -version` no longer fails on X11 connection

## If It Is Still Broken After Relogin

Then the problem is likely deeper in packaged `niri`/`xwayland-satellite` session auth handling, not in user config.

Next debugging targets:
- inspect the new session environment for `DISPLAY` and `XAUTHORITY`
- inspect fresh `journalctl --user -u niri.service -b`
- inspect whether the new X11 auth file is created anywhere under `/run/user/1000`
- if needed, apply a workaround for apps that do not need X11 at all, such as forcing PlantUML to Java headless mode
