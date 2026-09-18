# Workflow

Дата обновления: 2026-04-02
Владелец: admin-al
Область: system administration, configs, recovery context

## Core Rules

- Используй `~/ai/` как первый источник правил и recovery-контекста.
- Для изменений в `~/dotfiles` и `~/ai` завершенный дискретный шаг должен оканчиваться проверкой, коммитом и, если шаг готов, push.
- Для нетривиального `system work` всегда оставляй след в `~/ai/actions.log`.
- После завершенного системного изменения создавай или обновляй recovery-файл в `~/ai/recovery/`.
- Если меняется фактическое состояние системы, а не только текстовые заметки, обновляй `system_inventory` или помечай нужную секцию как stale.

## Что Считать System Work

- изменения в `~/.config`
- изменения в `~/.local/bin`
- shell-конфиги и login environment
- пакеты и package manager hooks
- `systemd --user` services и автозапуск
- network, DNS, proxy, SSH
- compositor, Wayland, terminal, notifications, clipboard
- bootstrap, migration, backup, restore
- любые действия вне git-репозитория, если они меняют систему или пользовательскую среду

## Logging Rules

- Веди хронологический лог в `~/ai/actions.log`.
- Каждая запись должна включать:
  - timestamp
  - что изменено
  - зачем изменено
  - статус проверки
  - откат или следующую ручную операцию, если она нужна
  - нужен ли relogin, restart или reboot

Пример:

```text
2026-04-02 18:20 MSK | Updated ~/.config/ssh/config and reloaded user ssh-agent environment | Why: normalize GitHub access on this machine | Verification: passed via ssh -T git@github.com | Rollback: restore previous ssh config from git | Relogin/Reboot: no
```

## Recovery File Rules

- Один нетривиальный системный эпизод должен иметь один понятный recovery trail.
- Recovery-файл должен содержать:
  - problem statement
  - findings
  - exact changes made
  - verification status
  - rollback strategy or note
  - relogin/restart/reboot requirement
  - next steps, если задача не исчерпана
- Предпочитай короткие, фактологичные и командно-ориентированные записи.

## Repo Rules

- `~/ai` хранит правила, заметки и системный operational context.
- `~/dotfiles` является основным репозиторием пользовательских конфигов и переносимой настройки среды.
- Если изменение затрагивает live-файл и соответствующий tracked-файл в `~/dotfiles`, держи их синхронными или явно фиксируй расхождение в recovery.
- Не вводи новые проектные реестры, базы и scaffolding, пока в этом нет реальной операционной необходимости.

## Inventory Rules

- `~/ai/system_inventory.json` и `~/ai/system_inventory_human.md` считаются первичным кэшем сведений о системе.
- Если нужная секция инвентаря свежая, не перепроверяй ее без причины.
- Перепроверяй точечно, если:
  - секция stale
  - секция invalidated
  - задача зависит от точной версии
  - пользователь просит явную проверку
  - есть признаки изменения окружения

## Minimum End-Of-Task Checklist

Перед завершением задачи:
1. проверить итоговое состояние файлов или сервисов
2. обновить `~/ai/actions.log`, если был system work
3. создать или обновить recovery trail в `~/ai/recovery/`, если изменение нетривиальное
4. закоммитить изменения в `~/ai` и/или `~/dotfiles`, если шаг завершен
5. при необходимости сделать `push`
6. отметить, нужен ли relogin, restart или reboot

## Notes

- `~/ai` это control plane, а не свалка произвольных заметок.
- `~/dotfiles` это основной источник истины для переносимых пользовательских конфигов.
- Архив импортированной истории хранится в `~/ai/archive/imported-home-pc/`.
- Если старые recovery-файлы относятся к другой машине или прошлому окружению, не используй их как активные правила без явной проверки релевантности.
