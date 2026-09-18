# Wiki.js: редактирование раздела `/ru/it` (2026-08-11)

## Симптом

Страницы раздела ИТ открывались для просмотра, но при переходе в редактор
`/e/ru/it/...` Wiki.js возвращал HTTP 500:

`Cannot create this page because it starts with a system reserved path.`

Проблема не связана с правами Бадмы Зубова: пользователь состоит в группах
`Administrators`, `Role-IT` и `ldap-users`.

## Причина

В Wiki.js первый сегмент пути из двух букв распознаётся как код локали.
`it` совпадает с ISO-кодом итальянской локали. Поэтому встроенная проверка
зарезервированных путей блокировала любой редакторский путь `ru/it/...` ещё до
загрузки существующей страницы.

## Исправление

На `spb-wiki` (`10.78.3.149`) создана резервная копия:

`/opt/wiki/server/controllers/common.js.bak-20260811-it-editor-route`

В `/opt/wiki/server/controllers/common.js` проверка зарезервированного пути
оставлена для всех путей, кроме уже используемого русскоязычного пространства
`ru/it` и его дочерних страниц. Затем перезапущен сервис:

```bash
sudo systemctl restart wiki.service
```

## Проверка

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/e/ru/it/sites
# 200

curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/e/ru/login/test
# 500 — защита остальных системных путей сохранена
```

## Откат

```bash
sudo cp /opt/wiki/server/controllers/common.js.bak-20260811-it-editor-route \
  /opt/wiki/server/controllers/common.js
sudo systemctl restart wiki.service
```

## Важно

Это точечный патч исходного файла Wiki.js. При обновлении Wiki.js проверить,
не был ли файл заменён, и при необходимости применить изменение повторно.
