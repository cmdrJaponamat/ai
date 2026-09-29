# Baseline: миграция существующих iSCSI fabric в VLAN

**Дата:** 2026-09-28  
**Статус:** read-only обследование; сетевые настройки MSA, PVE, H3C и NAS не менялись.

## Важное фактическое состояние

Подсети `10.78.4.0/24` и `10.78.5.0/24` сейчас физически разделены, но не
используют VLAN1040/VLAN1050. На обоих H3C команды `display vlan 1040` и
`display vlan 1050` вернули `This VLAN does not exist`. iSCSI endpoint-порты
работают с нетегированным VLAN1. Поэтому шаблонная матрица VLAN не описывает
фактическую production-конфигурацию этих фабрик.

## Рабочие iSCSI пути

| Ресурс | Fabric A | Fabric B |
|---|---|---|
| PVE1 | `10.78.4.11`, `ens2f0` | `10.78.5.11`, `ens2f1` |
| PVE2 | `10.78.4.12`, `ens2f0` | `10.78.5.12`, `ens2f1` |
| MSA LFF | `10.78.4.211` | `10.78.5.211` |
| MSA SFF | `10.78.4.221` | `10.78.5.221` |

На PVE1 и PVE2 все четыре iSCSI sessions `LOGGED_IN`; оба `mpath` имеют
active и enabled пути со статусом `ready/running`.

## Карта H3C

| Fabric | H3C | PVE1 | PVE2 | MSA SFF | MSA LFF |
|---|---|---|---|---|---|
| A / `.4` | upper `10.78.2.11` | `XGE1/0/49:1` | `XGE1/0/49:2` | `XGE1/0/51:1` | `XGE1/0/51:4` |
| B / `.5` | lower `10.78.2.12` | `XGE1/0/49:1` | `XGE1/0/49:2` | `XGE1/0/51:1` | `XGE1/0/51:3` |

Порты PVE на upper/lower уже hybrid: соответственно VLAN1060/1061 передаются
tagged для Corosync, а production iSCSI остаётся untagged VLAN1. Порты MSA
имеют дефолтную access-конфигурацию VLAN1. Эти MSA/PVE порты не менялись.

## Новая Synology

- `bond0` — `eth4`/`eth7`, active/standby, два 10GbE линка;
- действующий адрес файлового сервиса: `10.78.7.10/24` (VLAN1070);
- management: `10.78.0.250/24` на отдельном `eth1`;
- H3C upper/lower `XGE1/0/54:2` сейчас access VLAN1070;
- dynamic MAC указывает, что активный трафик NAS на момент проверки приходил
  через lower `XGE1/0/54:2`, несмотря на устаревшую подпись `standby`.

Перед любым физическим переключением кабели и соответствие `eth4`/`eth7`
портам H3C надо подтвердить на стойке.

## PVE3 и пустой NAS datastore

`eno3`/`eno4` PVE3 не имеют подключённых storage fabric и адресов `.4/.5`;
они не могут быть включены в новый NAS storage до отдельного физического
подключения. `10.78.4.10` не ответил на ICMP/ARP с PVE1 и на момент проверки
выглядит свободным, но это не заменяет reservation/IPAM проверку перед вводом.

`synology-exchange-dag` не содержит VM-дисков. Из него удален единственный
служебный файл моего прерванного benchmark (`.bench-raid10-final/seq.bin`,
5.25 GiB); после удаления `pvesm list` пуст и `du` показывает 0.

## Безопасный принцип будущей миграции

Не менять IP-адреса MSA или PVE и не трогать одновременно обе fabric.
Переводить сначала целиком Fabric A в VLAN1040 на её endpoint-портах, оставляя
Fabric B iSCSI active; подтвердить multipath/sessions/VM I/O, и только в другом
контрольном шаге переводить Fabric B в VLAN1050. Детальный change-план должен
включать console access, config backup обоих H3C и заранее определённые команды
rollback для всех четырёх endpoint-портов одной fabric.

## Доступ для операционного контроля PVE

Проверка PVE1/PVE2 в этой работе выполняется как `a.kuznetsov` по ключу
`~/.ssh/id_ed25519`. Не использовать для этой цели устаревшие password-записи
`root` в KeePass: они не прошли SSH-аутентификацию 2026-09-29.

## Выполнено: создание пустых VLAN, 2026-09-28

- H3C-1 / upper (`10.78.2.11`): создан VLAN `1040`, имя
  `STORAGE-FABRIC-A`;
- H3C-2 / lower (`10.78.2.12`): создан VLAN `1050`, имя
  `STORAGE-FABRIC-B`.

Перед изменением на каждом коммутаторе сохранён running-config во flash:
`prechange-storage-vlan1040-20260928.cfg` и
`prechange-storage-vlan1050-20260928.cfg` соответственно. Конфигурации
сохранены командой `save force`.

Проверка `display vlan` сразу после создания: в обоих VLAN нет ни tagged-, ни
untagged-портов. Следовательно, на этом этапе не менялись PVID, membership,
trunk/hybrid-настройки, MSA, PVE, IP-адреса или iSCSI-трафик. Попытка повторной
проверки iSCSI с этой рабочей станции не прошла из-за отсутствия действующего
SSH-ключа `ansible` к PVE1/PVE2; это не отражает состояние фабрик и требует
отдельного восстановления доступа/проверки с консоли PVE перед следующим
этапом.

## Выполнено: перевод production iSCSI в VLAN, 2026-09-29

### Fabric A — VLAN1040, H3C-1 / upper

| Endpoint | Порт | Итог |
|---|---|---|
| PVE1 `ens2f0` | `XGE1/0/49:1` | hybrid: VLAN1060 tagged, VLAN1040 untagged/PVID |
| PVE2 `ens2f0` | `XGE1/0/49:2` | hybrid: VLAN1060 tagged, VLAN1040 untagged/PVID |
| MSA (`10.78.4.221`) | `XGE1/0/51:1` | access VLAN1040 |
| MSA (`10.78.4.211`) | `XGE1/0/51:4` | access VLAN1040 |

### Fabric B — VLAN1050, H3C-2 / lower

| Endpoint | Порт | Итог |
|---|---|---|
| PVE1 `ens2f1` | `XGE1/0/49:1` | hybrid: VLAN1061 tagged, VLAN1050 untagged/PVID |
| PVE2 `ens2f1` | `XGE1/0/49:2` | hybrid: VLAN1061 tagged, VLAN1050 untagged/PVID |
| MSA (`10.78.5.221`) | `XGE1/0/51:1` | access VLAN1050 |
| MSA (`10.78.5.211`) | `XGE1/0/51:3` | access VLAN1050 |

На обоих наборах endpoint-портов VLAN1 исключён. Перед каждым этапом в flash
соответствующего H3C записан running-config:
`prechange-fabric-a-endpoints-20260929.cfg` и
`prechange-fabric-b-endpoints-20260929.cfg`.

Миграция выполнялась по одному endpoint-порту с проверкой между шагами. При
переводе PVE-порта кратковременно деградировали пути только этой фабрики;
вторая фабрика оставалась рабочей. После возвращения L2-связности выполнялись
`iscsiadm -m session --rescan`, `multipathd reconfigure` и `multipath -r` на
затронутом PVE, без изменения конфигурации PVE или MSA.

### Итоговая проверка

- на каждом PVE по 4 iSCSI sessions;
- все 8 путей суммарно (по 4 на PVE1/PVE2) имеют статус
  `active/running/ready`;
- PVE1 и PVE2 отвечают с соответствующих `ens2f0`/`ens2f1` до всех порталов
  `10.78.4.211`, `10.78.4.221`, `10.78.5.211`, `10.78.5.221`;
- `lvm_72t` и `lvm_pathb` active на обоих PVE; кластер `SPB-OBIT-DC` quorate
  3/3, config version 13.

### Откат

Откатывать только одну фабрику за раз и только при сохранённой другой фабрике.
На двух PVE-портах вернуть PVID и untagged membership в VLAN1, на двух
MSA-портах — `port access vlan 1`, затем выполнить iSCSI rescan и убедиться,
что два пути вновь `ready/running`. В качестве точного предизменённого
состояния использовать сохранённый во flash config соответствующего H3C;
не применять его целиком, чтобы не затронуть несвязанные изменения.
