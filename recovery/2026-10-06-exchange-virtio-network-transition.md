# Exchange DAG: переход e1000 → VirtIO Net

**Дата:** 2026-10-06  
**PVE:** `spb-pve1` (`10.78.2.201`)  
**VM:** `SPB-MX3` (117), `SPB-MX4` (135)

## Цель

Убрать ограничение около 1 Гбит/с, создаваемое эмулируемыми e1000 на двух
Exchange-серверах, и использовать VirtIO Net в том же `vmbr0`/VLAN без
изменения IP-плана и DAG-конфигурации.

## Выполнено

- На VM135 и VM117 добавлен второй адаптер VirtIO в `vmbr0` с первоначальным
  `link_down=1`.
- Windows на обеих ВМ обнаружил драйвер `Red Hat VirtIO Ethernet Adapter`.
- На MX4 новый адаптер получил прежние параметры `10.78.3.63/24`, шлюз
  `10.78.3.254`, DNS `10.78.3.50`; его линк поднят, старый e1000 отключён
  внутри Windows.
- На MX3 новый VirtIO получил прежние `10.78.3.62/24`, gateway `10.78.3.254`
  и DNS `10.78.3.50, 10.78.3.254`; линк поднят, старый e1000 отключён внутри
  Windows.
- До изменения сохранены `/root/135.conf.pre-virtio-net-20261006` и
  `/root/117.conf.pre-virtio-net-20261006` на PVE1.

## Проверка MX4

- VirtIO: `Up`, 10 Gb/s.
- ICMP до `10.78.3.63`: 5/5.
- MX4 разрешает MX3 в `10.78.3.62`; TCP/64327 (Exchange Replication) проходит
  через новый адаптер.
- AD secure channel на MX4 исправен.
- Все три созданные копии на MX4 — Healthy. На финальной проверке для
  `MailBoxDB_AL_new\\SPB-MX4`: CopyQueue 2, ReplayQueue 96.

## Проверка MX3 после переключения

- VirtIO: `Up`, 10 Gb/s; 5/5 ICMP до `10.78.3.62`.
- DNS разрешает MX4; TCP/64327 к MX4 проходит через VirtIO с source
  `10.78.3.62`.
- `nltest /sc_verify:aurora-logistics.local` возвращает `NERR_Success`.
- DAG `DAG02` видит MX2, MX3 и MX4 operational. Все network/cluster-проверки
  `Test-ReplicationHealth SPB-MX3` успешны.
- `DatabaseRedundancy` и `DatabaseAvailability` остаются failed только из-за
  известных старых `FailedAndSuspended` копий на MX2; это не регрессия сети.

## Наблюдение

Не удалять PVE `net0` и не удалять старый e1000 в Windows до согласованного
периода наблюдения: он является быстрым out-of-band откатом через QEMU Guest
Agent.

## Откат

Для MX4/MX3: через QEMU Guest Agent включить адаптер `Ethernet` (старый
e1000), вернуть на него соответствующие прежние IPv4/DNS, затем отключить
`Ethernet 2` (VirtIO). При необходимости удалить только `net1` в PVE по
сохранённым конфигам. Изменения в Exchange, DAG, IP-плане или сетевых
коммутаторах не выполнялись.
