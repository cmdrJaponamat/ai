# LegalDesk IMAP: тайм-аут и TLS — 2026-11-12

## Проблема

При сохранении включённого IMAP на странице `/admin/queues/mail` portal выдаёт `HESK bridge не ответил вовремя`.

## Причины

- На `10.78.3.1` имя `mail.aurora-logistics.ru` разрешается во внешний `85.114.6.214`, TCP 993 недоступен.
- Внутренний `10.78.3.62:993` доступен, но IMAP с IP отвергает TLS: сертификат `*.aurora-logistics.ru`, ошибка hostname mismatch.
- Общий тайм-аут portal bridge равен 5 с, меньше IMAP open timeout 8 с, поэтому при недоступном сервере UI получает неточную ошибку.

## Изменения

- На HESK-сервере `10.78.3.1` в `/etc/hosts` добавлено `10.78.3.62 mail.aurora-logistics.ru` после копии `/etc/hosts.before-hesk-imap-20261112`. Это даёт внутренний маршрут с проверяемым TLS-именем только на данном сервере.
- В bridge добавлена быстрая проверка TCP, отдельные сообщения о недоступности, сертификате и авторизации. Метод сохранения почты в PortalAL получил тайм-аут 20 с (коммит `143ca4f`). Обе live-копии bridge сохранены как `index.php.before-imap-connectivity-20261112` и обновлены.
- В legal HESK сохранён сервер `mail.aurora-logistics.ru` вместо IP при выключенном IMAP. Пароль не записывался, шаблоны писем не менялись.

## Проверка

- С HESK-сервера `getent` выдаёт `10.78.3.62`; TCP 993 открыт; OpenSSL TLS с `-verify_hostname mail.aurora-logistics.ru` даёт `Verification: OK`.
- IMAP с заведомо неправильными тестовыми данными возвращает `AUTHENTICATE failed`, то есть до аутентификации соединение проходит.
- Через production-коннектор неверные тестовые данные дают точный ответ `IMAP отклонил логин или пароль`; исходный legal-конфиг остался `enabled=false`, `passwordConfigured=false`.
- `php -l`, `npm run build`, CI и deploy `143ca4f` прошли; production-контейнер healthy. После развёртывания тест с неверными данными дал `IMAP отклонил логин или пароль` за 149 мс, а legal-конфиг остался `enabled=false`, `passwordConfigured=false`.

## Откат

Восстановить `/etc/hosts.before-hesk-imap-20261112`; откатить коммит `143ca4f` PortalAL и восстановить файлы bridge из `index.php.before-imap-connectivity-20261112`. Вернуть в legal HESK старый сервер IMAP `10.78.3.62` при выключенном чтении. Перезагрузка не требуется.
