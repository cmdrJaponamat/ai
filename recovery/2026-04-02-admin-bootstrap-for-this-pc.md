# Admin Bootstrap For This PC

## problem_statement

Нужно было переписать активные правила в `~/ai` под этот ПК: убрать учебно-проектный уклон, сфокусировать контекст на системном администрировании и подготовить launcher для `codex` с этими правилами.

## findings

- Текущие файлы `~/ai` были перенесены с другой машины и содержали старые пути `/home/japonamat`, учебные проекты, project DB и recovery trail, не относящиеся к этому ПК как к активному рабочему контексту.
- На этом ПК реально активны только два репозитория:
  - `/home/admin-al/ai`
  - `/home/admin-al/dotfiles`
- Готового launcher-скрипта в `~/.local/bin` не было.
- `codex` установлен в `/usr/bin/codex`.

## exact_changes_made

- Переписаны файлы:
  - `/home/admin-al/ai/ASSISTANT_BOOTSTRAP.md`
  - `/home/admin-al/ai/WORKFLOW.md`
  - `/home/admin-al/ai/RULES_HUMAN.md`
  - `/home/admin-al/ai/RULES.json`
  - `/home/admin-al/ai/PROJECT_CONTEXTS.md`
- Создан recovery-файл для самого репозитория `ai`:
  - `/home/admin-al/ai/.ai-recovery.md`
- Переписан recovery-файл `dotfiles` под текущие пути и роль:
  - `/home/admin-al/dotfiles/.ai-recovery.md`
- Добавлен launcher-скрипт:
  - `/home/admin-al/.local/bin/codex-ai-admin`
- Старые recovery-файлы, тематические заметки, старый `actions.log` и legacy-скрипт регистрации проектов вынесены в архив:
  - `/home/admin-al/ai/archive/imported-home-pc/`

## verification_status

- Новые Markdown-файлы прочитаны локально.
- `RULES.json` должен быть валидным JSON.
- Launcher должен проходить `bash -n`.

## rollback_strategy_or_note

- Откатить изменения в `~/ai` и `~/dotfiles` можно через git.
- Launcher можно удалить вручную:
  - `rm /home/admin-al/.local/bin/codex-ai-admin`

## relogin_restart_or_reboot_requirement

- Не требуется.

## next_steps

- При необходимости добавить WM hotkey для launcher отдельно.
- Освежить `system_inventory` уже под фактическое состояние этого ПК.
