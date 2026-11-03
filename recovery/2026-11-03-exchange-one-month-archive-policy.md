# Exchange: месячная политика переноса в онлайн-архив

Дата: 2026-11-03 09:33 MSK. По запросу владельца создан отдельный вариант политики для выборочного переноса писем старше 30 дней из основного ящика в Online Archive.

## Изменение

- На SPB-MX4 через PVE1 VM135 QEMU Guest Agent запущен локальный Exchange PowerShell snap-in от SYSTEM.
- Создан DPT-тег `1 month move to archive`: `Type=All`, `RetentionAction=MoveToArchive`, `AgeLimitForRetention=30` дней, `RetentionEnabled=True`.
- Создана политика `Default + 1month move to archive`: новый DPT и те же 10 общих тегов, что в `Default + 1year move to archive`.
- Политика не назначалась ящикам; существующие политики и теги не изменялись.

## Проверка

Readback Exchange: тег имеет срок 30 дней и действие MoveToArchive; политика содержит ровно 11 ожидаемых тегов, `IsDefault=False`, назначенных ящиков — 0.

## Откат и применение

До применения проверить отсутствие назначений, удалить сначала политику `Default + 1month move to archive`, затем тег `1 month move to archive`. Перезапуск служб, relogin и reboot не нужны.

Перед назначением конкретному ящику проверить наличие Online Archive, его свободную квоту и ожидаемый объём писем старше 30 дней. Политика перемещает письма, а не удаляет их.
