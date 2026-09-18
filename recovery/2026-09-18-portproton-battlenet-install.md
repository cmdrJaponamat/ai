# Battle.net через PortProton

Дата: 2026-09-18, MSK
Статус: установщик запущен; требуется ручное завершение в GUI.

## Цель

Установить Battle.net в отдельный Wine-префикс PortProton на локальном Arch Linux.

## Факты

- `portproton` уже был установлен из `pacman`: версия `1.7.5-1`.
- Использован штатный профиль `PW_BATTLE_NET` и runtime `PROTON_LG_10-28`.
- Автосценарий скачал официальный `Battle.net-Setup.exe` и запустил его через Wine.
- Создан префикс `/home/admin-al/PortProton/data/prefixes/BATTLE_NET`.
- До завершения GUI в префиксе уже присутствуют:
  - `drive_c/Program Files (x86)/Battle.net/Battle.net.exe`
  - `drive_c/Program Files (x86)/Battle.net/Battle.net Launcher.exe`

## Проверка

- Процесс `Battle.net-Setup.exe` активен через PortProton/Proton runtime.
- Wine prefix создан, `system.reg` присутствует.

## Следующие Шаги

1. В графическом окне завершить установку Battle.net.
2. Войти в аккаунт Battle.net вручную.
3. После первого запуска проверить вход в лаунчер и установить нужную игру.

## Откат

Закрыть установщик и удалить только `/home/admin-al/PortProton/data/prefixes/BATTLE_NET`.
PortProton и остальные префиксы не затрагивать.

## Перезапуск

Relogin, restart и reboot не требуются.
