# Ideco Unbound: отключение внешнего IPv6 DNS

Дата: 2026-08-31, MSK  
Устройство: `IDECO-SPB-PILOT` (`192.168.203.82`)

## Причина

У NGFW нет IPv6 default route, но штатный шаблон `dns-backend` содержал
`do-ip6: yes`. Unbound пытался обратиться к IPv6-адресам DNS-серверов и
засорял системный журнал сообщениями `Network is unreachable`.

## Изменение

В `/usr/share/ideco/dns-backend/unbound.conf.template` изменено только:

```text
do-ip6: yes
```

на:

```text
do-ip6: no
```

Затем перезапущены `ideco-dns-backend.service` для генерации
`/run/ideco-dns-backend/unbound.conf` и `unbound.service` для загрузки
конфигурации. Служебный IPv6 Ideco (`fc00:`) не изменялся.

## Проверка

- активный generated config содержит `do-ip6: no`;
- `ideco-dns-backend` и `unbound` active;
- запрос A-записи через `127.0.0.1` вернул `NOERROR`;
- после перезапуска сообщений Unbound о недоступном IPv6-маршруте не было.

## Откат

Оригинальный шаблон сохранён на Ideco:

`/var/lib/ideco-support/20260831-disable-unbound-ipv6/unbound.conf.template.before`

Восстановить его и применить:

```bash
cp -a /var/lib/ideco-support/20260831-disable-unbound-ipv6/unbound.conf.template.before \
  /usr/share/ideco/dns-backend/unbound.conf.template
systemctl restart ideco-dns-backend.service
systemctl restart unbound.service
```

Это изменение шаблона поставщика: после обновления Novum нужно проверить,
что `do-ip6: no` сохранился.
