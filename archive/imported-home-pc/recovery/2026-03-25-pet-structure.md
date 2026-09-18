## Problem

Нужно было выделить отдельное место в домашнем каталоге для pet-проектов, не связанных с учебой, и не смешивать их с заметками об идеях.

## Findings

- Каталог `/home/japonamat/pet` уже существовал.
- В нем уже лежали файлы с идеями: `IDEAS.md` и `VOICE_ASSISTANT_PROJECT.md`.
- Для проектов отдельной подструктуры не было.

## Exact Changes Made

- Создан каталог `/home/japonamat/pet/projects` для pet-проектов.
- Создан каталог `/home/japonamat/pet/ideas` для файлов с идеями.
- Файлы `IDEAS.md` и `VOICE_ASSISTANT_PROJECT.md` перенесены в `/home/japonamat/pet/ideas/`.

## Verification Status

Проверено командой `find /home/japonamat/pet -maxdepth 2 -mindepth 1 | sort`.
Ожидаемая структура существует:
- `/home/japonamat/pet/projects`
- `/home/japonamat/pet/ideas`
- существующие идеи находятся в `/home/japonamat/pet/ideas`

## Rollback

Ручной откат:
- перенести файлы из `/home/japonamat/pet/ideas/` обратно в `/home/japonamat/pet/`
- удалить пустые каталоги `/home/japonamat/pet/projects` и `/home/japonamat/pet/ideas`

## Relogin Or Reboot

Не требуется.

## Next Steps

- Новые pet-проекты создавать внутри `/home/japonamat/pet/projects/`.
- Идеи для pet-проектов сохранять в `/home/japonamat/pet/ideas/`.
- Проект `Photo_Trap` создавать по пути `/home/japonamat/pet/projects/Photo_Trap`.
