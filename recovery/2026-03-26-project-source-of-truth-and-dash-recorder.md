# Project Source Of Truth And Dash_Recorder

## problem_statement

Нужно было:
- отделить сценарий авторегистратора от `Photo_Trap`
- создать отдельный проект регистратора
- зафиксировать единый источник истины для проектного контекста

## findings

- `Photo_Trap` и авторегистратор имеют общую техническую базу, но разные продуктовые сценарии и UX.
- Смешивание их в один продукт размывает release scope `Photo_Trap`.
- Для долгоживущих проектов нужен один явный источник истины по состоянию проекта.

## exact_changes_made

- В `Photo_Trap` обновлены `docs/ROADMAP.md` и `.ai-recovery.md`:
  - авторегистратор больше не считается естественным режимом внутри `Photo_Trap`
  - он зафиксирован как отдельный продукт на общей технической базе
- Создан новый проект:
  - `/home/japonamat/pet/projects/Dash_Recorder`
  - `/home/japonamat/pet/projects/Dash_Recorder/.ai-recovery.md`
  - `/home/japonamat/pet/projects/Dash_Recorder/docs/ROADMAP.md`
  - `/home/japonamat/pet/projects/Dash_Recorder/README.md`
- Обновлен реестр:
  - `~/ai/PROJECT_CONTEXTS.md`
- В общих правилах закреплено, что источником истины по проекту по умолчанию является `project-root/.ai-recovery.md`:
  - `~/ai/WORKFLOW.md`
  - `~/ai/ASSISTANT_BOOTSTRAP.md`
  - `~/ai/RULES.json`

## verification_status

- Проверено чтением файлов и структуры каталогов.
- Для `Photo_Trap` изменения дополнительно будут проверены через `git status` и отдельный коммит.
- Для `Dash_Recorder` создан минимальный проектный скелет без git-репозитория.

## rollback_strategy_or_note

- Правки в `Photo_Trap` можно откатить через git.
- Правки в `~/ai` откатываются вручную по этому recovery-файлу или через локальный git, если он позже будет настроен.
- Новый каталог `Dash_Recorder` можно удалить вручную, если проект решат не вести.

## relogin_or_reboot_requirement

- Не требуется.
