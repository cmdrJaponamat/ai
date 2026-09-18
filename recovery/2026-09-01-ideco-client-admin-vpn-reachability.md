# Откат: доступ Admin VPN к Ideco Client

Дата: 2026-09-01

## Изменение

На RouterOS `AL-SPB-MILLION` добавлены:

- маршрут `10.128.0.0/24` через `172.31.146.2`;
- два разрешающих правила `forward` перед финальным `drop` для трафика между
  Admin VPN `10.78.90.32/27` и Ideco Client / транзитом Ideco.

На `AL-OBIT` добавлен маршрут `10.128.0.0/24` через активный
`ovpn-spb-office`. Правило `Allow admin-vpn anywhere` уже разрешает всю
подсеть `10.78.90.32/27`, поэтому отдельные адресные исключения не нужны.

Это восстанавливает симметричный L3-путь к VPN-адресу клиента и ответам
физического адреса клиента, когда он отправляет их через Ideco Client.

## Откат на RouterOS

```routeros
/ip route remove [find comment="Ideco Client VPN pool return route"]
/ip firewall filter remove [find comment="Ideco Client VPN pool to Admin VPN"]
/ip firewall filter remove [find comment="Ideco transit to Admin VPN"]
```

На `AL-OBIT`:

```routeros
/ip route remove [find comment="Ideco Client VPN pool via SPB OVPN"]
```
