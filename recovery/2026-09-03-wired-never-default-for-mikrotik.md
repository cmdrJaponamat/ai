# Проводное подключение к запасному MikroTik без default route

Дата: 2026-09-03. Хост: `AL-KUZNETSOV-AR`.

## Цель

Использовать прямое проводное соединение с запасным MikroTik для диагностики,
не позволяя DHCP/RA этого соединения заменить основной маршрут через Wi-Fi/VPN.

## Исходное состояние

- NetworkManager-профиль: `Проводное подключение 1`;
- UUID: `e8d0d6ef-f094-3dd4-9991-2b72ca21fb73`;
- интерфейс: `enp195s0f0`;
- IPv4/IPv6 method: `auto`;
- `ipv4.never-default=no`, `ipv6.never-default=no`;
- во время изменения carrier отсутствовал, профиль был неактивен;
- действующие default routes шли только через Wi-Fi `wlp194s0`.

## Изменение

```bash
nmcli connection modify uuid e8d0d6ef-f094-3dd4-9991-2b72ca21fb73 \
  ipv4.never-default yes ipv6.never-default yes
```

Профиль сохраняет DHCP/SLAAC и autoconnect, но не принимает роль default route.

## Проверка

Readback показывает `never-default=yes` для IPv4 и IPv6. Текущие IPv4/IPv6
default routes остались на `wlp194s0`. Проверка с активным Ethernet ожидает
появления физического carrier.

## Откат

```bash
nmcli connection modify uuid e8d0d6ef-f094-3dd4-9991-2b72ca21fb73 \
  ipv4.never-default no ipv6.never-default no
```

Relogin/reboot не требуются. Если профиль активен, после отката переподнять
только это проводное соединение.
