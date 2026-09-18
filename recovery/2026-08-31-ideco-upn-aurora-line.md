# Ideco: альтернативный UPN `aurora-line.com`

Дата: 2026-08-31, MSK  
Устройство: `IDECO-SPB-PILOT` (`192.168.203.82`)

## Изменение

В настройках AD-домена `aurora-logistics.local` добавлен альтернативный
UPN-суффикс `aurora-line.com`. Список теперь содержит:

- `aurora-logistics.ru`;
- `aurora-line.com`.

Это позволяет Ideco сопоставлять учётные записи вида
`user@aurora-line.com` с тем же AD-доменом.

## Хранение и проверка

Изменён ключ etcd:

`/ad/domains/settings/v8/records/4c5e7c76-461b-4b29-a383-51926b2a6bab`

Точная резервная копия до изменения находится на Ideco:

`/var/lib/ideco-support/20260831-ideco-upn-aurora-line/domain-settings.before.json`

Итоговая конфигурация прочитана обратно; `ideco-agent-backend` и
`ideco-agent-websocket` активны.

## Откат

```bash
ETCDCTL_ENDPOINTS=http://127.0.0.1:2379 \
etcdctl put /ad/domains/settings/v8/records/4c5e7c76-461b-4b29-a383-51926b2a6bab \
  "$(cat /var/lib/ideco-support/20260831-ideco-upn-aurora-line/domain-settings.before.json)"
```

После отката пользователю нужно переподключиться в Ideco Client.
