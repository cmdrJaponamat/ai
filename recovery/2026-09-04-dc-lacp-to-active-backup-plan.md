# Переход cross-switch LACP на active-backup в ЦОД

Дата: 2026-09-04. Статус: окно A завершено 2026-09-06; окно B (Synology) ожидает отдельного согласования.

## Цель

Убрать LACP-группы, участники которых подключены к двум независимым H3C без
IRF/MLAG. Перевести PVE1–PVE3, uplink `AL-OBIT` и Synology `spb-file` на
active-backup, сохранив отказоустойчивость между upper/lower.

## Почему изменение необходимо

Каждый endpoint видит два разных LACP partner system ID:

- upper: `60da-8377-74dc`;
- lower: `60da-8376-cbe6`.

Поэтому один slave попадает в активный aggregator, второй остаётся отдельным
Unselected/churned aggregator. Это не единый отказоустойчивый LAG. Та же ошибка
присутствует у PVE, MikroTik и четырёхпортового bond Synology.

## Подтверждённая карта на 2026-09-04

| Endpoint | Endpoint bond | Upper H3C | Lower H3C | Текущее состояние |
|---|---|---|---|---|
| PVE1 | `bond0`: `enp61s0f0np0`, `enp61s0f1np1` | `XGE1/0/2`, BAGG1, Selected | `XGE1/0/3`, BAGG2, Unselected | реально работает upper |
| PVE2 | `bond0`: `enp61s0f0np0`, `enp61s0f1np1` | `XGE1/0/3`, BAGG2, Unselected | `XGE1/0/2`, BAGG1, Selected | реально работает lower |
| PVE3 | `bond0`: `eno1`, `eno2` | `XGE1/0/4`, BAGG3, Unselected | `XGE1/0/4`, BAGG3, Selected | вероятно lower/`eno2`; нужна физическая сверка |
| AL-OBIT | `LAG-SW`: `sfp-sfpplus1`, `sfp-sfpplus2` | `XGE1/0/54:1`, BAGG100, Unselected | `XGE1/0/54:1`, BAGG100, Selected | реально работает lower |
| Synology | `bond0`: `eth0`–`eth3` | `XGE1/0/21`,`22`, BAGG4, оба Selected | `XGE1/0/21`,`22`, BAGG4, оба Unselected | реально работают два upper-порта |

PVE1/PVE2 имеют 10 Гбит/с на каждом slave. На PVE3 сейчас `eno1` согласован
на 100 Мбит/с, `eno2` — на 1 Гбит/с; до миграции требуется проверить кабель,
порт и реальное соответствие `eno1/eno2` H3C. Synology использует четыре
1-Гбит/с порта, DSM 7.2.2-72806 Update 9, `bond0=10.78.2.210/24`, MTU 1500.

На H3C эти BAGG работают в untagged VLAN 1. Отдельные management-подключения
AL-OBIT `ether3`→upper и `ether4`→lower находятся в VLAN 1000 и не входят в
изменяемый uplink; их запрещено трогать.

## Критическая зависимость Synology и Exchange DAG

NFS `10.78.2.210:/volume1/main` подключён как storage `synology` ко всем PVE.
Только VM 111 `spb-mx2` использует его для работающих дисков:

- `virtio1`: 7800 ГБ;
- `virtio2`: 1700 ГБ;
- `virtio3`: 600 ГБ;
- `virtio4`: 20 ГБ.

Системный диск VM 111 находится на local-zfs PVE2. Другой Exchange-участник
`spb-mx3` (VM 117) хранит диски на MSA `lvm_pathb`. Нельзя одновременно
менять uplink PVE2 и bond Synology; Synology выполняется отдельным окном.

## Обязательные допуски

Перед началом всего проекта:

1. Согласовать два окна: A — AL-OBIT/PVE, B — Synology/Exchange.
2. Иметь локальную/BMC-консоль каждого PVE, локальный доступ к AL-OBIT и DSM.
3. Снять и сохранить current/startup-конфигурации обоих H3C, export/backup
   RouterOS, `/etc/network/interfaces` всех PVE и DSM configuration backup.
4. Проверить quorum 3/3, links 0/1/2 Corosync, HA, storage, bridge/VLAN,
   bond state, STP, MAC и ошибки портов.
5. Не начинать при деградации Corosync, storage, DAG, HA или физического link.
6. На каждом endpoint менять только один контур и завершать его приёмку до
   перехода к следующему.
7. Не удалять BAGG-интерфейс, пока последний endpoint-member не переведён и
   откат не исключён.

## Базовый алгоритм без потери обоих путей

Для каждого endpoint:

1. Определить фактически Selected и Unselected slave по endpoint и обоим H3C.
2. Вывести **только Unselected** switch-port из его BAGG (`undo port
   link-aggregation group ...`), оставить/задать standalone access VLAN 1.
3. Подтвердить, что текущий LACP продолжает работать через Selected member.
4. На endpoint переключить bond в active-backup, временно назначив primary тот
   slave, чей H3C-порт уже standalone. Проверить перенос MAC и доступность.
5. Теперь прежний Selected slave стал standby: вывести его switch-port из BAGG
   и сделать тем же standalone access VLAN 1.
6. После проверки обоих standalone-путей выбрать постоянный primary и
   зафиксировать политику reselect.
7. Проверить отказ primary, работу standby, автоматическое восстановление и
   отсутствие MAC flapping. Только затем сохранить H3C/endpoint config.

Нельзя сначала вывести из BAGG оба порта: это создаёт гарантированный разрыв
между LACP endpoint и standalone-коммутаторами.

## Окно A. AL-OBIT и PVE

### A1. Перевести AL-OBIT

1. Проверить работу отдельных management-портов `ether3`/`ether4` и иметь
   локальную консоль MikroTik.
2. Upper `XGE1/0/54:1` сейчас Unselected: вывести только его из BAGG100 и
   настроить standalone access VLAN 1, не меняя `ether3`/VLAN1000.
3. Убедиться, что `LAG-SW` продолжает работать через lower.
4. Перевести `LAG-SW` с `802.3ad` на `active-backup`, временный primary —
   `sfp-sfpplus1` (upper standalone); сохранить slaves, MAC, bridge membership,
   MTU и VLAN table без изменений.
5. Проверить gateway/VLAN 804–807/1000, DHCP, маршрутизацию, firewall counters,
   RSTP и доступность PVE.
6. Вывести lower `XGE1/0/54:1` из BAGG100 и сделать идентичным standalone
   access VLAN 1.
7. Проверить failover в обе стороны. Постоянный primary выбрать осознанно;
   рекомендуемый — lower `sfp-sfpplus2`, поскольку это текущий рабочий путь.

Стоп: потеря management, VLAN, DHCP, route или изменение STP вне ожидаемого.

### A2. Перевести PVE1

- Unselected сначала: lower `XGE1/0/3` / `enp61s0f1np1`.
- Временный primary active-backup: `enp61s0f1np1`.
- Затем вывести upper `XGE1/0/2` из BAGG1.
- После двухстороннего теста рекомендуемый постоянный primary:
  `enp61s0f0np0` (upper).

### A3. Перевести PVE2

- Выполнять не одновременно с Synology.
- Unselected сначала: upper `XGE1/0/3` / `enp61s0f1np1`.
- Временный primary: `enp61s0f1np1`.
- Затем вывести lower `XGE1/0/2` из BAGG1.
- После теста рекомендуемый постоянный primary:
  `enp61s0f0np0` (lower).

### A4. Перевести PVE3 последним

Сначала физически/через controlled link test подтвердить соответствие H3C
портов `eno1/eno2` и устранить согласование `eno1` на 100 Мбит/с, если это не
ограничение оборудования. Предполагаемая, но не разрешённая без проверки карта:
upper→`eno1` (Unselected), lower→`eno2` (Selected).

После подтверждения применить базовый алгоритм. Временный primary — уже
standalone upper slave; постоянный primary — исправный более быстрый путь.

### Конфигурация Linux bond

На каждой PVE через штатный Proxmox API изменить только `bond0`:

```text
bond-mode active-backup
bond-miimon 100
bond-primary <проверенный slave>
bond-primary-reselect always
```

Удалить параметры, специфичные только для 802.3ad: `bond-lacp-rate` и
`bond-xmit-hash-policy`. Не менять slaves, `vmbr0`, IP, gateway, VLAN, MTU,
Corosync или storage NIC. Перед apply проверить pending diff. После reload:
SSH/BMC, VM traffic, `cat /proc/net/bonding/bond0`, quorum, Corosync links,
HA, storage, failed units и журналы.

После каждой PVE имитировать отказ только текущего primary switch-port;
standby должен принять MAC и трафик без потери quorum/HA. Восстановить порт и
проверить согласованное reselect-поведение до следующей PVE.

## Окно B. Synology и Exchange

### B1. Подготовить DAG

Exchange-администратор должен выполнить и сохранить результаты:

```powershell
Get-DatabaseAvailabilityGroup -Status | Format-List
Get-MailboxDatabaseCopyStatus * | Format-Table -Auto
Test-ReplicationHealth
```

Все базы должны иметь здоровую актуальную копию вне `spb-mx2`. Перенести
активные базы с `spb-mx2` на `spb-mx3`/другой подтверждённый DAG-member и
повторить проверки. Запретить автоматическую активацию копий на `spb-mx2` на
время окна либо перевести сервер в DAG maintenance по принятой процедуре.

Затем чисто остановить Exchange/VM 111. Убедиться, что ни одна другая running
VM и ни одна backup/restore/replication задача не пишет в storage `synology`.
Временно disable storage в Proxmox и добиться корректного unmount NFS на всех
узлах. Не продолжать при зависшем mount или I/O.

### B2. Подтвердить физическую карту NAS

LACP actor index показывает upper ports 21/22 и lower 21/22, но точное
соответствие DSM `eth0`–`eth3` не доказано. Определить его по одному порту через
DSM identify/controlled shutdown и H3C counters. Зафиксировать таблицу до
изменения.

### B3. Перевести Synology bond

1. Сделать DSM configuration backup и отдельный recovery-доступ через
   неиспользуемый `eth4=10.78.2.211` либо `eth5=10.78.2.212`, если это безопасно
   и физически доступно.
2. Вывести два lower-порта (сейчас Unselected) из BAGG4 и сделать standalone
   access VLAN 1. Upper LACP должен продолжить работу.
3. В DSM изменить Bond 1 с IEEE 802.3ad на Active/Standby, сохранив
   `10.78.2.210/24`, gateway `10.78.2.254`, MTU 1500 и DNS.
4. В момент изменения primary должен быть физический slave на уже standalone
   lower-порту. Если DSM не позволяет детерминированно сделать это без
   пересоздания bond, выполнять только при остановленной VM 111 и отключённом
   storage, с локальным доступом DSM.
5. После переноса MAC на lower вывести upper `XGE1/0/21` и `22` из BAGG4 и
   сделать standalone access VLAN 1.
6. Предпочтительно сохранить все четыре исправных slave в Active/Standby,
   если DSM GUI поддерживает такой состав и показывает один Active/три Standby.
   Если DSM ограничивает режим двумя портами, оставить по одному физическому
   порту на upper/lower, а два остальных административно отключить с точной
   маркировкой и записью, не оставлять их standalone вне bond.
7. Проверить один primary и standby на другом H3C, MAC только на активном
   порту, отсутствие loop/MAC flapping и фактическую пропускную способность
   1 Гбит/с.

### B4. Вернуть сервис

1. Включить storage `synology`, подтвердить NFSv4.1 mount и read/write probe
   штатными средствами Proxmox без изменения дисков VM.
2. Запустить VM 111 и проверить Windows event log, диски, Exchange services.
3. Повторить `Get-MailboxDatabaseCopyStatus *` и `Test-ReplicationHealth`;
   дождаться Healthy/Synchronized перед возвратом активационной политики.
4. Выполнить контролируемый отказ активного Synology slave во время наблюдения
   за NFS latency/I/O, но без одновременного failover PVE или DAG.
5. Подтвердить отсутствие NFS timeout, hung task, VM I/O errors и разрыва DAG.

## Приёмка всего проекта

- На H3C отсутствуют endpoint-members в BAGG1–4/100; старые пустые BAGG можно
  удалить только отдельным финальным шагом после истечения rollback window.
- PVE1–PVE3: один active и один standby, оба физически UP; failover проверен.
- AL-OBIT: один active/один standby, все bridge VLAN и L3-сервисы работают.
- Synology: один active и минимум один standby на разных H3C; NFS стабилен.
- Corosync links 0/1/2 connected, quorum 3/3, HA штатно.
- Storage PVE соответствует baseline, нет I/O и network errors.
- Exchange DAG Healthy/Synchronized; активные базы возвращены только после
  отдельного решения Exchange-администратора.
- H3C startup, RouterOS, PVE и DSM конфигурации сохранены; мониторинг slave
  интерфейсов и NFS/DAG включён.

## Откат

Откатывать только текущий endpoint и только с локальной/BMC-консоли:

1. Вернуть bond endpoint в `802.3ad` с исходными slave/options.
2. Вернуть оба его порта в исходные BAGG на соответствующих H3C.
3. Проверить Selected/Unselected baseline, MAC, connectivity и сохранить.

Для Synology перед откатом VM 111 должна быть остановлена, storage disabled,
DAG базы активны вне `spb-mx2`. Восстановить DSM configuration/bond0 и BAGG4,
затем NFS, VM и DAG. Не откатывать другие уже принятые endpoints.

## Следующее действие

Проверить BMC/консоль PVE1, снять его prechange snapshot и выполнить A2.
Synology остаётся отдельным последним окном после явного подтверждения здоровья
Exchange DAG.

## Фактическое выполнение: AL-OBIT, 2026-09-06

- Перед изменением подтверждены мобильный WAN SSH, quorum 3/3, Corosync links
  0/1/2, HA и storage. RouterOS backup/export созданы заранее.
- Upper `XGE1/0/54:1` был Unselected и первым выведен из BAGG100; он оставлен
  standalone access VLAN 1 с описанием
  `AL-OBIT-sfp1-standalone-active-backup`.
- `LAG-SW` через WAN-сессию переведён с 802.3ad на active-backup; при первом
  переносе MAC потерян один начальный ping, связь восстановилась примерно за
  69 мс.
- После переноса трафика на upper lower `XGE1/0/54:1` выведен из BAGG100 и
  оставлен standalone access VLAN 1 с описанием
  `AL-OBIT-sfp2-standalone-active-backup`.
- Постоянный primary задан `sfp-sfpplus2` (lower); `sfp-sfpplus1` — standby.
- Контролируемый shutdown active lower-порта немедленно перевёл трафик на
  upper. 10/10 ping PVE1 и 5/5 ping Synology прошли без потерь, quorum и все
  Corosync links сохранились. После `undo shutdown` lower автоматически снова
  стал active.
- Оба H3C сохранены в `flash:/startup.cfg`; пустые BAGG100 оставлены на время
  rollback window.
- Итоговые RouterOS файлы:
  `post-al-obit-active-backup-20260906.backup` и `.rsc`.
- Итоговая проверка: все три WAN SSH доступны; PVE quorum 3/3; Corosync links
  0/1/2 connected; Synology NFS и остальные ожидаемые storage active; failed
  units отсутствуют.

Откат AL-OBIT: вернуть `LAG-SW` в 802.3ad и последовательно вернуть оба
`XGE1/0/54:1` в BAGG100, либо использовать prechange backup при локальном
доступе. Не восстанавливать полный backup удалённо поверх новых изменений.

## Фактическое выполнение: PVE1–PVE3, 2026-09-06

- До изменений подтверждены доступ через HDM/iLO, quorum 3/3, Corosync links
  0/1/2, HA, storage и отсутствие failed units. На каждом PVE сохранена копия
  `/etc/network/interfaces` в `/root/interfaces.pre-active-backup-*`.
- PVE1: lower `XGE1/0/3` первым выведен из BAGG2; `bond0` переведён в
  active-backup; затем upper `XGE1/0/2` выведен из BAGG1. Постоянный primary —
  upper `enp61s0f0np0`, lower `enp61s0f1np1` — standby; оба 10 Гбит/с.
- PVE2: upper `XGE1/0/3` первым выведен из BAGG2; затем lower `XGE1/0/2`
  выведен из BAGG1. Постоянный primary — lower `enp61s0f0np0`, upper
  `enp61s0f1np1` — standby; оба 10 Гбит/с.
- PVE3: controlled flap подтвердил карту `eno1`→upper XGE1/0/4 и
  `eno2`→lower XGE1/0/4 и восстановил согласование `eno1` со 100 Мбит/с до
  1 Гбит/с. Оба порта выведены из BAGG3. Постоянный primary — lower `eno2`,
  upper `eno1` — standby; оба 1 Гбит/с.
- На всех PVE persistent-конфигурация содержит `bond-mode active-backup`,
  `bond-miimon 100` и проверенный `bond-primary`; LACP rate и transmit hash
  удалены. Runtime показывает `primary_reselect always`.
- Первый reload PVE1/PVE2 временно оставлял в ядре прежний active slave, хотя
  primary уже был в конфигурации; управление восстановлено через независимый
  Corosync-link и запись `primary`/`active_slave` в sysfs. Повторные reload
  persistent-конфигураций прошли по 120/120 проб без потерь.
- Первый переход PVE3 на standalone upper занял около 3,7 секунды (37 из 160
  частых ICMP-проб); quorum и Corosync links 1/2 не прерывались.
- Контролируемое отключение permanent primary проверено на каждом PVE:
  PVE1, PVE2 и PVE3 дали 10/10 ответов через standby; quorum 3/3, Corosync
  links 0/1/2 и storage сохранились. После возврата портов primary
  автоматически выбрался снова.
- Upper/lower H3C XGE1/0/2–4 оставлены standalone access VLAN 1 с точными
  описаниями endpoint/slave. BAGG1–3 оставлены пустыми на rollback window.
  Оба H3C сохранены в `flash:/startup.cfg`.
- Итоговая приёмка: все slave UP, gateway и Synology доступны с каждого PVE,
  storage active, HA/watchdog штатны, failed units отсутствуют.

Окно B с Synology и VM111 не выполнялось и остаётся отдельной работой.

## Исправление доступа H3C в KeePass, 2026-09-06

- В записи `Сеть/ЦОД H3C S6800` пароль был верным, но имя пользователя
  `manage` было неверным. Повторная проверка `manage` и `manege` дала отказ на
  обоих H3C; `admin` успешно вошёл на `10.78.2.11` и `10.78.2.12`.
- Имя пользователя исправлено на `admin`, notes актуализированы.
- До изменения создана копия
  `/home/admin-al/work/passwords.kdbx.pre-h3c-username-fix-20260906-173407`.
- Откат: при закрытом KeePassXC вернуть указанную копию, предварительно
  сохранив более новые изменения базы; предпочтительнее вручную вернуть только
  username/notes записи, если после копии база менялась.
