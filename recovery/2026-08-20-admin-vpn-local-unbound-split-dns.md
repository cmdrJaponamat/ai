# Локальный Unbound для split-DNS административного VPN

## Назначение

Локальный Unbound на этом ПК служит системным DNS-резолвером. Он направляет
только зону `aurora-logistics.local` к корпоративному Unbound `10.78.4.253`.
Маршрут к этому адресу проходит через `tun0` административного OpenVPN.
Остальные зоны передаются на `8.8.8.8` и `1.1.1.1`.

## Файлы

- `/etc/unbound/unbound.conf.d/aurora-split-dns-test.conf` — правило
  пересылки и настройки локального резолвера;
- `/etc/resolv.conf` — указывает на `127.0.0.1`;
- `/etc/NetworkManager/conf.d/90-local-unbound.conf` — запрещает
  NetworkManager перезаписывать `resolv.conf`.

## Проверка

```bash
systemctl is-active unbound
dig @127.0.0.1 spb-dc1-al.aurora-logistics.local A
dig @127.0.0.1 example.com A
ip route get 10.78.4.253
```

Ожидаемый ответ для `spb-dc1-al.aurora-logistics.local` — `10.78.3.50`;
маршрут к `10.78.4.253` — через `tun0` при активном admin-vpn.

## Особенность DNSSEC

В Unbound включён `val-permissive-mode: yes`: DNS-ответы текущей сетевой
оболочки не сохраняют необходимую для строгой проверки DNSSEC цепочку.
До внедрения Unbound системный резолвер DNSSEC также не валидировал.

## Откат

Восстановить файлы `.bak-20260820-*`, созданные сценарием активации; удалить
`/etc/NetworkManager/conf.d/90-local-unbound.conf`; затем выполнить:

```bash
sudo systemctl restart unbound
sudo systemctl restart NetworkManager
```
