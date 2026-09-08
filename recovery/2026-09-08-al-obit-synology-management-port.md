# Management-порт новой Synology на AL-OBIT

Дата: 2026-09-08. Статус: порт подготовлен, кабель ещё не подключён.

## Выполнено

- На AL-OBIT выбран ранее свободный и не включённый в bridge `ether13`.
- `ether13` добавлен в `bridge` как endpoint access-порт:
  - PVID 1000;
  - только untagged/priority-tagged ingress;
  - ingress filtering;
  - edge=yes.
- `ether13` добавлен в untagged membership VLAN1000 `DC-MGMT-INFRA`.
- Для management MAC новой Synology RS3618xs `90:09:D0:32:EF:6A` создана
  статическая DHCP lease `10.78.0.10` на `vlan1000(mgmt)-dhcp`.

10G-интерфейсы Synology, VLAN1070, H3C, LAG-SW, маршрутизация и firewall не
изменялись.

## Резервная копия

На AL-OBIT созданы и проверены:

- `pre-synology-mgmt-ether13-20260908.backup`;
- `pre-synology-mgmt-ether13-20260908.rsc`.

## Проверка

- persistent readback: ether13 PVID1000 и untagged VLAN1000;
- DHCP lease существует и ожидает клиента;
- ether13 `no-link`, что ожидаемо до подключения кабеля;
- существующие management endpoints 10.78.0.11 и 10.78.0.253 отвечают 3/3;
- SSH-доступ к AL-OBIT сохранён.

После подключения management-интерфейса Synology к физическому порту 13
ожидается lease `10.78.0.10/24`, gateway/DNS `10.78.0.254`.

## Откат

1. Удалить статическую lease с comment `new Synology RS3618xs management`.
2. Удалить только bridge-port entry `ether13`.
3. Удалить `ether13` из untagged списка VLAN1000, сохранив остальные порты.

Аварийный откат с локальной консоли возможен из named backup. Reboot/relogin
не требуется.
