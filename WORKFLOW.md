# Workflow

Date created: 2026-03-13
Owner: japonamat
Scope: local system work, config changes, recovery context

## Core Rules

- Log all system-level actions into `~/ai/`.
- Commit every change under `~/.config` immediately after each discrete action.
- Create or update a recovery/context file in `~/ai/` after every completed task or system change.
- Если в любом контексте появляется стоящая идея для пет-проекта, ее нужно обязательно записать в отдельный файл в `~/pet/`, независимо от текущей задачи.

## Logging Rules

- Keep a plain chronological log in `~/ai/actions.log`.
- Each log entry should include:
  - timestamp
  - what was changed
  - why it was changed
  - whether verification passed
- If a task is risky or unfinished, write the rollback or next-step note in the same entry.

Example:
```text
2026-03-13 15:10 MSK | Changed ~/.config/niri/autostart.sh | Removed manual dbus env import because niri 25.11 already manages Xwayland | Verification pending until relogin
```

## Config Change Rules

- Any change inside `~/.config` should be treated as its own discrete action.
- After each discrete `.config` change:
  1. verify the file content
  2. commit the change
  3. update recovery notes in `~/ai/`
- Do not batch unrelated `.config` changes into one commit.

## Recovery File Rules

- Every completed task should leave a recovery trail in `~/ai/`.
- Recovery files should contain:
  - problem statement
  - findings
  - exact changes made
  - verification status
  - next steps
- Prefer one focused file per topic, plus this general workflow file.

## Suggested Files In `~/ai`

- `WORKFLOW.md` — persistent working rules
- `actions.log` — chronological action log
- topic files like:
  - `niri-x11-context.md`
  - `niri-x11-checklist.md`

## Правила Для Идей Пет-Проектов

- Все стоящие идеи для пет-проектов хранить в `~/pet/`.
- Фиксировать идеи даже тогда, когда текущая задача не связана с разработкой.
- Для каждой идеи кратко записывать:
  - цель проекта
  - почему идея интересна
  - возможный стек
  - минимальный MVP

## Minimum End-Of-Task Checklist

Before considering a task complete:
1. log the action in `~/ai/actions.log`
2. if `~/.config` changed, commit it
3. update or create a recovery file in `~/ai/`
4. record verification result

## Notes

- `~/ai/` is the first place to look when restoring context.
- Recovery notes should be short, factual, and command-oriented.
