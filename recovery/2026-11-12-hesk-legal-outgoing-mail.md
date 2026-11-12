# Исходящая почта и отбивка HESK Legal — 2026-11-12

## Задача и причина

Письма в legal HESK читаются и заявки создаются, но заявитель не получает подтверждение. Live-конфиг legal: `smtp=0`, `notify_new=0`, `noreply_mail=it@aurora-logistics.ru`, bridge `mail_enabled=false`.

## Изменения

- На странице `/admin/queues/mail` добавить независимый блок SMTP и отбивки для каждой очереди.
- Через HMAC bridge читать и писать SMTP host/port/шифрование, адрес и имя отправителя, учётные данные, `notify_new`. Пароль в ответах скрыт. Возможность взять текущие IMAP-учётные данные без копирования пароля через браузер.
- Проверять SMTP соединение и авторизацию без отправки сообщения перед включением.
- Для legal установлен `LegalDesk@aurora-logistics.ru`, `mail.aurora-logistics.ru:587`, STARTTLS; SMTP и `notify_new=1` включены после успешной проверки авторизации. Bridge разрешает почтовые уведомления legal, когда SMTP включён.
- Почтовые шаблоны не менять.

## Проверка

- `npm run build`, `php -l`, CI и deploy PortalAL `1839ab0` прошли; production-контейнер healthy.
- На сервере HESK проверены SMTP connect, STARTTLS и AUTH существующими IMAP-учётными данными LegalDesk без отправки письма: `smtp_auth_ok`.
- Через production-коннектор выполнены GET/POST/GET исходящих настроек legal; readback совпал. Live HESK: `smtp=1`, `notify_new=1`, отправитель и SMTP login `LegalDesk@aurora-logistics.ru`, пароль сохранён. IT-почтовый конфиг не менялся.
- Фактическая доставка отбивки на новое входящее письмо пока не проверена. Ранее созданные заявки автоматически не получают задним числом подтверждение.

## Откат

Восстановить `/root/hesk-legal-settings-before-outgoing-20261112.php` в `/var/www/hesk-legal/html/hesk_settings.inc.php` с владельцем `www-data:www-data` и режимом `0640`, а bridge из `index.php.before-outgoing-20261112` в обеих каталогах `/opt/hesk-{portal,legal-portal}-bridge/`; revert коммита `1839ab0` PortalAL и push. Перезагрузка ОС не требуется, контейнер портала развёртывается автоматически.
