# Refactor Counter Rule

## problem_statement

Нужно добавить в общий AI-контекст на ПК правило для coding work: после нескольких дискретных шагов разработки выполнять обязательный рефакторинговый проход, а не откладывать его бесконечно.

## findings

- Правила в `~/ai` уже описывают git, system work и recovery trail, но не задают явный порог для рефакторинга во время кодинга.
- Для текущего режима работы по `Photo_Trap` удобен простой и повторяемый порог: `3` дискретных feature/fix шага.
- Это правило должно жить и в человекочитаемых Markdown-файлах, и в машинном `RULES.json`.

## exact_changes_made

- Добавлено общее правило `refactor counter` в `/home/japonamat/ai/ASSISTANT_BOOTSTRAP.md`.
- Добавлен раздел `Coding Rules` в `/home/japonamat/ai/WORKFLOW.md`.
- Добавлена секция `coding_policy` в `/home/japonamat/ai/RULES.json`.
- Зафиксирован порог: после `3` завершенных дискретных feature/fix шагов выполнять отдельный рефакторинговый проход и затем сбрасывать счетчик.

## verification_status

- Проверка пройдена чтением обновленных файлов `~/ai`.
- Формат `RULES.json` сохранен валидным JSON.

## rollback_strategy_or_note

- Откат ручной: удалить добавленные разделы из `ASSISTANT_BOOTSTRAP.md`, `WORKFLOW.md` и `RULES.json`.
- Если позже правило окажется слишком жестким, изменить только `refactor_counter_threshold`, не удаляя саму политику.

## relogin_or_reboot_requirement

- Не требуется.

## next_steps

- Использовать это правило по умолчанию во всех новых coding-сессиях.
- При необходимости позже вынести счетчик и текущее значение в отдельный проектный recovery-шаблон.
