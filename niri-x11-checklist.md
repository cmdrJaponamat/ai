# Niri X11 Checklist

## After Relogin

Run:
```bash
xdpyinfo | head
xprop -root
plantuml -version
```

## Current Fixes Already Applied

```bash
sed -n '1,40p' ~/.config/niri/autostart.sh
systemctl --user disable xwayland-satellite.service
```

## If X11 Is Still Broken

Check session environment:
```bash
echo "$XDG_SESSION_TYPE"
echo "$XDG_CURRENT_DESKTOP"
echo "$DISPLAY"
echo "$WAYLAND_DISPLAY"
echo "$XAUTHORITY"
```

Check X11/Xwayland state:
```bash
ps -ef | rg 'niri|Xwayland|xwayland-satellite'
ls -la /tmp/.X11-unix
xdpyinfo | head
```

Check logs:
```bash
journalctl --user -u niri.service -b --no-pager | tail -n 200
```

## Recovery Rule

After each system/config action:
```bash
date '+%F %T %Z' >> ~/ai/actions.log
```
