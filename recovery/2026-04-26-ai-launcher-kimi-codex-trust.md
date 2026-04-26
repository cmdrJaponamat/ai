# AI launcher: Kimi fix and Codex project trust

## Problem

Через хоткей `Mod+Shift+A` после выбора `Kimi` и проекта окно быстро закрывалось. Для `Codex` требовалось сделать trust выбранной директории проекта явным при запуске.

## Findings

- В лаунчерах `Kimi` запуск шел через `bash -lc`, где `kimi` не находился по `PATH`.
- Логи `~/.kimi/logs/kimi.log` показывали симптомы запуска без нормального терминала: `Input is not a terminal`, `Inappropriate ioctl for device`, `Broken pipe`.
- Unified launcher и standalone launcher для `Codex` передавали рабочую директорию только через `alacritty --working-directory`, но не задавали явный trust для конкретного выбранного проекта.

## Changes

- В `scripts/ai-launcher` и установленной копии `~/.local/bin/ai-launcher`:
  - добавлен явный резолв путей к `codex` и `kimi`;
  - запуск переведен на `alacritty --command ...` без промежуточного `bash -lc`;
  - `Codex` теперь получает:
    - `-C <project_dir>`
    - `-c 'projects."<project_dir>".trust_level="trusted"'`
  - `Kimi` теперь получает прямой вызов `kimi --context <tmpfile>`.
- В `scripts/kimi-ai-launcher-json` и `~/.local/bin/kimi-ai-launcher-json`:
  - убран запуск через shell;
  - добавлен явный поиск бинаря `kimi`.
- В `scripts/codex-ai-launcher-json` и `~/.local/bin/codex-ai-launcher-json`:
  - убран запуск через `bash -lc`;
  - добавлены `-C <project_dir>` и явный runtime trust override.

## Verification

- Синтаксис всех шести скриптов проверен через `compile(..., 'exec')` в памяти.
- Проверено, что в установленной копии `ai-launcher` используется прямой `alacritty --command`.
- Проверено, что у `Kimi` используется резолв `~/.local/bin/kimi`.
- Проверено, что `Codex` получает явный override `projects."<project_dir>".trust_level="trusted"`.

## Rollback

- Для отката вернуть старые версии:
  - `~/.local/bin/ai-launcher`
  - `~/.local/bin/kimi-ai-launcher-json`
  - `~/.local/bin/codex-ai-launcher-json`
  - `scripts/ai-launcher`
  - `scripts/kimi-ai-launcher-json`
  - `scripts/codex-ai-launcher-json`
- Если изменения закоммичены, откат предпочтительно делать через `git revert` для файлов в `/home/japonamat/ai`.
- Установленные копии в `~/.local/bin` при необходимости откатываются ручной заменой из git-версий или предыдущих резервных копий.

## Relogin/Reboot

Не требуется.

## Next steps

- Проверить реальный запуск через хоткей `Mod+Shift+A` в графической сессии.
- Если `Kimi` все еще закрывается, собрать свежий хвост `~/.kimi/logs/kimi.log` после нового запуска.
