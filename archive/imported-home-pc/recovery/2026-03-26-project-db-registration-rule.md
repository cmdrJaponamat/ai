# Project DB Registration Rule

## problem_statement

Нужно было закрепить правило, что при создании нового проекта надо обновлять не только `PROJECT_CONTEXTS.md`, но и `~/ai/projects.db`, а также дать для этого простой локальный инструмент.

## findings

- `projects.db` используется как индекс проектов и должен обновляться при появлении новых project recovery-источников.
- Ручной SQL неудобен и повышает шанс ошибок или пропуска обновления.
- Главным источником истины по проекту остается `.ai-recovery.md`, а база данных только индексирует проект.

## exact_changes_made

- Обновлены правила:
  - `~/ai/WORKFLOW.md`
  - `~/ai/ASSISTANT_BOOTSTRAP.md`
  - `~/ai/RULES.json`
- Добавлен скрипт:
  - `~/ai/projects/register_project.sh`
- Скрипт делает upsert записи в `projects`
- Если передан `remote_url`, скрипт добавляет `origin` в `project_remotes`
- Скрипт проверен на существующем проекте:
  - `Dash_Recorder`

## verification_status

- Скрипт успешно выполнился локально.
- `sqlite`-запросы показали корректные записи для `Photo_Trap` и `Dash_Recorder`.
- `RULES.json` остался валидным JSON.

## rollback_strategy_or_note

- Удалить `~/ai/projects/register_project.sh`
- Откатить правки в `WORKFLOW.md`, `ASSISTANT_BOOTSTRAP.md`, `RULES.json`
- При необходимости удалить или исправить записи в `~/ai/projects.db` вручную через `sqlite3`

## relogin_or_reboot_requirement

- Не требуется.
