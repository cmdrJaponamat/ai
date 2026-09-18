# KDE Meta Return To Alacritty

Date: 2026-04-02
Host: AL-KUZNETSOV-DE

## Problem Statement

Нужно было сделать так, чтобы `Win+Enter` в текущей KDE Plasma сессии открывал `alacritty` вместо `Konsole`.

## Findings

- В текущем live-файле [kglobalshortcutsrc](/home/admin-al/.config/kglobalshortcutsrc) `Meta+Return` был назначен на `Konsole`.
- В системе есть desktop entry `/usr/share/applications/Alacritty.desktop`.
- Из текущей terminal-сессии нет подтверждённого доступа к user DBus, поэтому live-reload `kglobalaccel` не удалось верифицировать.

## Exact Changes Made

- Создан backup: `/home/admin-al/.config/kglobalshortcutsrc.bak-2026-04-02-win-enter-alacritty`
- В [kglobalshortcutsrc](/home/admin-al/.config/kglobalshortcutsrc) изменено:
  - `[services][org.kde.konsole.desktop]` `_launch=Ctrl+Alt+T`
  - добавлено `[services][Alacritty.desktop]` `_launch=Meta+Return`

## Verification Status

- Файл проверен локально: `Meta+Return` теперь прописан для `Alacritty.desktop`
- У `Konsole` оставлен `Ctrl+Alt+T`, конфликт по `Meta+Return` убран
- Вызов DBus-методов для немедленной перезагрузки hotkeys не подтверждён из-за sandbox-доступа к `/run/user/1000/bus`

## Rollback Strategy

- Восстановить backup:
  - `cp ~/.config/kglobalshortcutsrc.bak-2026-04-02-win-enter-alacritty ~/.config/kglobalshortcutsrc`
- Либо вручную вернуть `_launch=Ctrl+Alt+T\tMeta+Return` в секции `org.kde.konsole.desktop` и удалить секцию `Alacritty.desktop`

## Relogin Restart Reboot

- Relogin: maybe
- Restart: maybe `kglobalaccel` or Plasma session reload if hotkey does not apply immediately
- Reboot: no

## Next Steps

- Проверить `Win+Enter` вручную в GUI-сессии
- Если хоткей не применился сразу, перелогиниться в Plasma
