# Imported History Archived

## problem_statement

После переписывания правил под этот ПК в `~/ai` все еще оставалась импортированная история с другой машины: старые recovery-файлы, тематические заметки, legacy-скрипт под project DB и старый `actions.log`.

## findings

- Эти файлы относились к другому пользователю, другим путям и другому рабочему контексту.
- Держать их в активных каталогах `~/ai/recovery/` и корне `~/ai/` было вредно для навигации и повышало риск случайно принять старый контекст за актуальный.

## exact_changes_made

- Создан архивный каталог:
  - `/home/admin-al/ai/archive/imported-home-pc/`
- В архив перенесены:
  - старые recovery-файлы в `/home/admin-al/ai/archive/imported-home-pc/recovery/`
  - тематические заметки в `/home/admin-al/ai/archive/imported-home-pc/topical/`
  - legacy-скрипт `register_project.sh` в `/home/admin-al/ai/archive/imported-home-pc/projects/`
  - старый журнал действий в `/home/admin-al/ai/archive/imported-home-pc/actions.imported.log`
- Создан новый пустой активный лог:
  - `/home/admin-al/ai/actions.log`

## verification_status

- Перенос проверен просмотром итоговой структуры `~/ai`.
- Активный каталог `~/ai/recovery/` теперь содержит только заметки, относящиеся к этому ПК.

## rollback_strategy_or_note

- При необходимости файлы можно вручную вернуть из `/home/admin-al/ai/archive/imported-home-pc/` на прежние места.
- Для обычной работы откат не нужен.

## relogin_restart_or_reboot_requirement

- Не требуется.
