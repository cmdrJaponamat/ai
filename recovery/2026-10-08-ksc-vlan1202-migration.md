# KSC: перенос в VLAN1202

Дата: 2026-10-08. VM113 `spb-ksc` на PVE2.

## Итог

KSC перенесён с legacy untagged bridge в `VLAN1202` (`DC-SECURITY-MGMT`):

| Параметр | До | После |
| --- | --- | --- |
| IP KSC | `10.78.20.97/27` | `10.78.20.98/27` |
| Шлюз KSC | `10.78.20.126` | `10.78.20.97` |
| PVE NIC | `vmbr0`, untagged | `vmbr0`, tag `1202` |
| Шлюз подсети | legacy bridge `.126` | `VLAN1202-DC-SECURITY-MGMT` `.97` |

## Сохранённые точки

- PVE snapshot: `pre-vlan1202-20261008`;
- конфигурация VM: `/root/113.conf.pre-vlan1202-20261008` на PVE2;
- RouterOS export: `pre-ksc-vlan1202-20261008` на AL-OBIT;
- KSC network backup:
  `/etc/systemd/network/5-static.network.pre-vlan1202-20261008`.

## Проверка

- ICMP с AL-OBIT и PVE2 к `10.78.20.98`: 3/3;
- SSH по ключу доступен на `.98`;
- `https://10.78.20.98:8080/login` возвращает HTTP 200;
- KSC разрешает и достигает `spb-dc1-al.aurora-logistics.local`
  (`10.78.3.50`);
- address-lists `SharedSrvs`, `KSC Distribution point` и
  `IdecoPilotSharedSrvs` обновлены на `.98`.

## Откат

Через PVE console VM113 восстановить прежний файл сети, снять VLAN tag 1202,
на AL-OBIT выключить SVI VLAN1202 и включить `10.78.20.126/27` на legacy bridge.
Затем вернуть `.98` в затронутых address-lists обратно на `.97`.
