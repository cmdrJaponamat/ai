# Инцидент: Unbound возвращал SERVFAIL для внешних имён

Дата: 2026-08-13, MSK.

## Симптом

Сеть на Миллионной имела исправный маршрут до `10.78.4.253` через OVPN:
`10/10` ICMP без потерь. Доменная зона
`aurora-logistics.local` отвечала через `spb-dc1-al`, но запросы внешних
имён (`ya.ru`, `google.com`, `cloudflare.com`) к Unbound получали `SERVFAIL`.

## Причина

В момент инцидента Unbound потерял связь с единственным прежним upstream
`77.88.8.8`, а затем временно пометил оба новых forwarder как недоступные.
При таком состоянии он немедленно возвращал клиентам `SERVFAIL`. Параллельно
поток повторных запросов от клиентов превысил прежний размер очереди (1024
запроса на поток), что усиливало эффект.

Транспорт от Миллионной до ЦОДа и доменная зона
`aurora-logistics.local` работали. Это не был отказ OVPN, WireGuard или AD DNS.

## Изменение

На `spb-vpn-srv` в `/etc/unbound/unbound.conf.d/local.conf` заменён один
forwarder `77.88.8.8` на два независимых:

```conf
forward-zone:
    name: "."
    forward-first: yes
    forward-addr: 1.1.1.1
    forward-addr: 8.8.8.8
```

`forward-first: yes` оставляет внешние resolver основным путём, но разрешает
Unbound перейти к обычному рекурсивному разрешению, если оба forwarder
временно недоступны.

Добавлен `/etc/unbound/unbound.conf.d/20-capacity.conf`:

```conf
server:
    num-threads: 4
    num-queries-per-thread: 4096
    outgoing-range: 8192
    outgoing-num-tcp: 64
    incoming-num-tcp: 64
    serve-expired: yes
    serve-expired-ttl: 86400
    serve-expired-reply-ttl: 30
    serve-expired-client-timeout: 500
```

После изменения очищены служебная оценка доступности upstream и кэш:

```bash
sudo unbound-control flush_infra all
sudo unbound-control flush_zone .
```

Перед изменением сохранена копия:

```text
/root/incident-backups/local.conf.2026-08-13-143503
```

Проверка конфигурации и reload:

```bash
sudo unbound-checkconf
sudo systemctl reload unbound
```

## Проверка результата

- `dig @127.0.0.1 ya.ru A +dnssec` — `NOERROR`;
- `dig @127.0.0.1 google.com A +dnssec` — `NOERROR`;
- `dig @127.0.0.1 cloudflare.com A +dnssec` — `NOERROR`;
- `dig @10.78.4.253 aurora-logistics.local A` — `NOERROR`;
- из `AL-SPB-MILLION` до `10.78.4.253` — `10/10` ICMP, потерь нет.

Проверка прямого обращения к трём DNS root-серверам также вернула `NOERROR`.

## Откат

```bash
sudo cp -a /root/incident-backups/local.conf.2026-08-13-143503 \
  /etc/unbound/unbound.conf.d/local.conf
sudo rm -f /etc/unbound/unbound.conf.d/20-capacity.conf
sudo unbound-checkconf && sudo systemctl reload unbound
```

Перезагрузка сервера не требуется.
