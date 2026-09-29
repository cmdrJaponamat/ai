# SPB-NAS1: подготовка связности reverse proxy для Synology Drive

**Дата:** 2026-09-29  
**NAS:** `SPB-NAS1` / `spb-file-cloud`  
**Reverse proxy:** `10.78.3.1` (`nginx`)

## Цель

Подготовить минимальный внутренний transport path для будущего веб-доступа к
Synology Drive через `cloud.aurora-logistics.ru`. DSM не публикуется напрямую
в Internet.

## Изменение

На `AL-OBIT` включено заранее подготовленное правило RouterOS:

```text
comment: STORAGE-FILE staged: reverse proxy to Drive
chain: forward
action: accept
protocol: tcp
src-address: 10.78.3.1
dst-address-list: STORAGE-FILE (SPB-NAS1 = 10.78.7.10)
dst-port: 5001
```

Правило было расположено после финального `[DROP_ALL]`, поэтому не работало.
Оно перенесено непосредственно перед этим запретом. Других firewall/NAT-правил
не добавлялось и не изменялось.

## Проверка

С reverse proxy выполнено:

```bash
curl -k -I --connect-timeout 10 https://10.78.7.10:5001
```

Результат: `HTTP/2 200`; счетчик правила на RouterOS увеличился.

## Выполненная конфигурация

- `SynologyDrive 4.0.3-27892` установлен и запущен вместе с официальными
  зависимостями. `Synology Office` намеренно не устанавливался.
- NAS остаётся в `AURORA-LOGISTICS.LOCAL`; успешный `wbinfo --ping-dc`
  подтверждён до `spb-dc1-al.aurora-logistics.local` (`10.78.3.50`).
- `share` включена как единственная Synology Drive Team Folder. Папка
  `pve-exchange-dag` не индексируется Drive и не публикуется.
- В DSM Login Portal для Synology Drive включён штатный псевдоним `drive`.
  Виртуальный хост Nginx перенаправляет только корень
  `https://cloud.aurora-logistics.ru/` на `/drive/`, поэтому пользователь
  сразу открывает Drive, а маршруты публичных ссылок `/d/...` не меняются.
- На `share` выданы RW ACL `@AURORA-LOGISTIC\\App-Cloud-Links` и владельцу
  `AURORA-LOGISTIC\\admin-al`; исходные административные ACL сохранены.
- Для public links: только участники AD-группы `App-Cloud-Links`, обязательный
  пароль, максимальный срок действия 3 дня, HTTPS и базовый URL
  `https://cloud.aurora-logistics.ru`.
- На reverse proxy создан `/etc/nginx/conf.d/cloud.aurora-logistics.ru.conf`.
  Он принимает HTTP только для ACME и перенаправляет его на HTTPS; HTTPS
  проксирует к `https://10.78.7.10:5001`. Для обычных запросов Nginx повторно
  использует upstream-соединения; WebSocket-upgrade передаётся только при
  фактическом запросе upgrade. Прямого интернет-доступа к DSM нет.
- Выпущен отдельный Let's Encrypt сертификат
  `cloud.aurora-logistics.ru`, срок действия до `2026-12-28`; автоматическое
  продление настроено Certbot.
- Проверено: запрос через Nginx и по публичному имени возвращает `HTTP 200`.
  После оптимизации 48 параллельных запросов к ресурсу Drive через публичное
  имя завершились `200/48`.

## Осознанно не включено

`File Request` (внешняя загрузка на NAS по ссылке) выключен. Для обычной
выдачи файлов он не нужен: пользователь кладёт файл в `share`, создаёт
защищённую ссылку, получатель скачивает файл в браузере. Включение File Request
требует отдельной онлайн-активации расширенных функций Synology Drive.

## Следующие действия

1. Добавить нужных сотрудников в `AURORA-LOGISTIC\\App-Cloud-Links`.
2. Провести один пилот: сотрудник создаёт ссылку на тестовый файл из `share`,
   проверяются пароль, срок и URL `cloud.aurora-logistics.ru`.
3. При необходимости входящей загрузки отдельно согласовать онлайн-активацию
   расширенных функций Drive и выделить изолированную папку назначения.

## Откат

На reverse proxy удалить vhost и перезагрузить Nginx:

```bash
sudo unlink /etc/nginx/conf.d/cloud.aurora-logistics.ru.conf
sudo nginx -t && sudo systemctl reload nginx
```

После этого на `AL-OBIT` отключить transport rule:

```routeros
/ip firewall filter disable [find where comment="STORAGE-FILE staged: reverse proxy to Drive"]
```

Это закрывает внешний веб-доступ и transport path `10.78.3.1 → 10.78.7.10:5001`;
SMB, NFS, management NAS и другие опубликованные сервисы не затрагиваются.

**Relogin/restart/reboot:** не требуется.

## Инцидент безопасности — 2026-09-29

После публикации выяснено, что vhost проксировал не изолированный Drive-only
endpoint, а также DSM/API-маршруты (`/webapi/`, `/webman/`). Это противоречит
исходной формулировке выше о непубликации DSM и является ошибкой архитектуры
публикации. В журнале Nginx зафиксированы внешние запросы к `.env`, `.git` и
DSM API с адресов, не относящихся к администратору или reverse proxy. Это
подтверждает сканирование; успешная компрометация не подтверждена и не может
быть исключена без NAS-side журналов.

Пользователь изолировал NAS от reverse proxy firewall-правилом. Проверка с
`10.78.3.1` в 16:xx MSK: TCP `10.78.7.10:5001` завершается таймаутом. Сам vhost
на Nginx пока включён, поэтому после расследования его следует отключить также
отдельно как второй рубеж изоляции.

Неизменяемая локальная копия access log сохранена вне Git в
`/home/admin-al/ai/incident-evidence/2026-09-29-synology-public-exposure/`;
SHA-256 зафиксирована в `README.md`. Следующий безопасный этап: восстановить
контролируемый административный доступ к NAS, прежде чем менять учётные записи,
и собрать NAS-side журналы/аудит пользователей и групп.
