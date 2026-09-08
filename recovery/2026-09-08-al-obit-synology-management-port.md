# Management-порт новой Synology на AL-OBIT

Дата: 2026-09-08. Статус: Synology фактически подключена через ether14.

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

## Фактическое подключение через ether14

Пользователь оставил на `ether13` бывший Corosync MikroTik, а management-порт
Synology подключил к отдельному физическому порту 14. Поэтому:

- `ether14` переведён из legacy PVID1 в untagged-only access VLAN1000;
- существующая DHCP-резервация Synology сохранена без изменения;
- Synology MAC `90:09:D0:32:EF:6A` получил `10.78.0.10` с hostname
  `Diskstation`;
- линк ether14 — 1 Гбит/с full duplex;
- TCP/5000 DSM доступен через маршрутизируемую management-сеть;
- ether13 оставлен access VLAN1000, но подписан
  `spare MikroTik mgmt switch - not commissioned`; конфигурация самого
  MikroTik не менялась.

Дополнительные backup/export AL-OBIT:

- `pre-synology-mgmt-ether14-20260908.backup`;
- `pre-synology-mgmt-ether14-20260908.rsc`.

Временный адрес `10.78.0.252/24`, добавленный Ethernet-профилю ноутбука для
прямой диагностики, удалён; исходные `192.168.88.2/24` и `10.78.3.253/24`
сохранены, default route на Ethernet не добавлялся.

## Откат

Для отката только фактического подключения Synology вернуть `ether14` в
PVID1/admit-all и удалить только `ether14` из untagged списка VLAN1000.
DHCP lease удалять только при полном отказе от management-адреса полки.

Первоначальный ether13 откатывается отдельно: удалить его bridge-port entry и
убрать только ether13 из untagged списка VLAN1000.

Аварийный откат с локальной консоли возможен из named backup. Reboot/relogin
не требуется.
