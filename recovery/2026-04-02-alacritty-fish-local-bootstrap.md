# Alacritty And Fish Local Bootstrap

Date: 2026-04-02
Host: AL-KUZNETSOV-DE

## Problem Statement

Нужно было установить `alacritty` и `fish`, подключить конфиги из `~/dotfiles`, но адаптировать их к локальным ограничениям этой машины, чтобы не сломать текущую среду.

## Findings

- На машине отсутствовали `fish` и `alacritty`.
- В live-среде отсутствовали `~/.config/fish` и `~/.config/alacritty`.
- В [alacritty.toml](/home/admin-al/dotfiles/alacritty/alacritty.toml) был зашит путь `/bin/fish`, которого нет на Debian-машине.
- В fish-конфигах были безусловные зависимости на Oh My Fish и `pokemon-colorscripts`, которые на машине не установлены.
- В alacritty-конфиге был указан `JetBrainsMono Nerd Font`, которого на машине нет; доступен `Hack`.
- `most` на машине не установлен, поэтому для `PAGER` нужен fallback.

## Exact Changes Made

- Установлены пакеты `fish` и `alacritty` через `apt`.
- Обновлён [alacritty.toml](/home/admin-al/dotfiles/alacritty/alacritty.toml):
  - shell changed to `/usr/bin/fish`
  - font changed from `JetBrainsMono Nerd Font` to `Hack`
- Обновлён [config.fish](/home/admin-al/dotfiles/fish/config.fish):
  - `pokemon-colorscripts` запускается только если бинарь существует
  - `PAGER` выставляется в `most`, а при его отсутствии в `less`
- Обновлён [omf.fish](/home/admin-al/dotfiles/fish/conf.d/omf.fish):
  - OMF загружается только если существует `init.fish`
- Созданы симлинки:
  - `~/.config/fish -> /home/admin-al/dotfiles/fish`
  - `~/.config/alacritty -> /home/admin-al/dotfiles/alacritty`
- Login shell пользователя не менялся.

## Verification Status

- `command -v fish` -> `/usr/bin/fish`
- `fish --version` -> `fish, version 4.0.2`
- `command -v alacritty` -> `/usr/bin/alacritty`
- `alacritty --version` -> `alacritty 0.15.1`
- `fish -ic 'printf "shell=%s\npager=%s\n" $FISH_VERSION $PAGER'` passed and returned `shell=4.0.2`, `pager=less`
- Проверено, что оба live-каталога в `~/.config` подключены симлинками к `~/dotfiles`
- Попытка запустить `alacritty` из неинтерактивной terminal-сессии завершилась `WaylandError(Connection(NoCompositor))`; это не подтверждает ошибку конфига, а только показывает отсутствие compositor-доступа в текущем запуске

## Rollback Strategy

- Удалить симлинки `~/.config/fish` и `~/.config/alacritty`
- Удалить пакеты `fish` и `alacritty` через `sudo apt-get remove fish alacritty`, если они больше не нужны
- Вернуть конфиги в `~/dotfiles` через git revert или restore нужных файлов

## Relogin Restart Reboot

- Relogin: no
- Restart: no
- Reboot: no

## Next Steps

- Если нужно, отдельно переключить login shell на `fish` через `chsh -s /usr/bin/fish`
- При следующем обновлении системного инвентаря учесть, что на машине теперь установлены `fish` и `alacritty`
