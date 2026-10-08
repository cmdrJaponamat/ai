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

## Исправление IAM после миграции

После смены IP Web Console оставалась на странице «Служба аутентификации
недоступна». Причина: её конфигурация обращается к IAM по
`ksc.aurora-logistics.ru:9050`, но имя внутри KSC разрешалось не в новый
адрес. На KSC добавлено постоянное локальное сопоставление
`10.78.20.98 ksc.aurora-logistics.ru` в `/etc/hosts` и cloud-init шаблон
`/etc/cloud/templates/hosts.debian.tmpl` (предыдущие версии сохранены с
суффиксом `.pre-ksc-fqdn-20261008`). После перезапуска только
`KSCWebConsole` и `KSCSvcWebConsole` запрос к IAM вернул ожидаемый `401
unauthorized`, а `/login` перестал отдавать страницу недоступности IAM.

## Откат

Через PVE console VM113 восстановить прежний файл сети, снять VLAN tag 1202,
на AL-OBIT выключить SVI VLAN1202 и включить `10.78.20.126/27` на legacy bridge.
Затем вернуть `.98` в затронутых address-lists обратно на `.97`.
