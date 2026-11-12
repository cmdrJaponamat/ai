# Почта очередей портала и HESK — 2026-11-12

## Задача

Страница администратора для настройки источника входящих писем каждой очереди. Портал передаёт изменения через HMAC-коннектор в соответствующий экземпляр HESK.

## Состояние до изменений

- ИТ: IMAP включён, загрузчик HESK запускается из root crontab каждую минуту.
- Юристы: IMAP выключен, отдельного расписания загрузчика нет; пароль ящика не получен.
- Обе копии HESK держат параметры IMAP в `hesk_settings.inc.php`, файл и каталог принадлежат `www-data`.

## Изменения

- Код: PortalAL, страница `/admin/queues/mail`, API `/api/service-desk/queues/{it|legal}/mail/incoming`, методы HMAC bridge GET/POST.
- Bridge пишет только разрешённые поля IMAP, проверяет соединение перед включением, возвращает только признак наличия пароля.
- Live bridge обновляется в `/opt/hesk-{portal,legal-portal}-bridge/index.php` с резервными копиями; почтовые шаблоны не изменяются.
- Для юридической очереди добавлен `/etc/cron.d/hesk-legal-imap` (каждую минуту от `www-data`); скрипт ничего не импортирует при `imap=0`.
- Параметры LegalDesk записаны на backend: `10.78.3.62:993`, SSL, `LegalDesk@aurora-logistics.ru`, `imap_keep=1`, без пароля и без включения IMAP.

## Проверка

- `npm run build` прошёл; `php -l` на сервере для обеих копий bridge прошёл.
- Публикация PortalAL: коммиты `6b62424`, `94bcf9d`, `b041d5a`; итоговый CI/deploy прошёл, production-контейнер `portal-al:b041d5a` healthy.
- Через production-коннектор прочитаны разные настройки ИТ и юридической очередей. После записи на legal немедленное чтение сначала показало старые значения из OPcache; добавлен `opcache_invalidate()`, повторный тест записи и немедленного чтения дважды прошёл.
- Ручной запуск загрузчика legal при `imap=0`: exit 0, сообщение `IMAP FETCHING IS DISABLED IN SETTINGS`.
- Страница `/admin/queues/mail` вернула HTTP 200; API без сессии вернул HTTP 401. Пароль через API не выдаётся. Проектная заметка обновлена в `assistent` (коммит `2d0d340`).
- Остаётся получить пароль LegalDesk и согласовать импорт старых писем перед включением IMAP.

## Откат

Портал: revert коммитов PortalAL и push в main. Bridge: восстановить `/opt/hesk-portal-bridge/index.php.before-mail-settings-20261112` и `/opt/hesk-legal-portal-bridge/index.php.before-mail-settings-20261112`. Расписание: удалить `/etc/cron.d/hesk-legal-imap`. Конфиг HESK: выключить IMAP в настройках либо вручную вернуть прежние значения `imap_host_name=mail.example.com`, `imap_user=''`, `imap_keep=0`. Перезагрузка ОС не требуется; для применения bridge может потребоваться перезапуск PHP-FPM при включённом постоянном OPcache.
