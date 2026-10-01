# Переход хранилища EXCH-3 с NFS на iSCSI

Дата: 2026-10-01

## Цель

Заменить NFS-backed хранилище, подготовленное для будущего третьего участника
Exchange DAG (`EXCH-3`), на block storage через Synology iSCSI.

## Причина

Microsoft не поддерживает хранение данных Exchange на NAS, представленном
гостевой ВМ через гипервизор. `cache=none` снижает риск write-back cache, но
не меняет тип хранилища. Для Exchange DB/log требуется block-level storage.

## Подтверждённое исходное состояние

- Proxmox storage `synology-exchange-dag` указывал на
  `10.78.5.10:/volume2/pve-exchange-dag` с NFSv4.1.
- На нём отсутствовали VM-диски: `pvesm list synology-exchange-dag` был пуст.
- В конфигурациях VM не найдено ссылок на этот storage.
- Выделенный пул Synology `/volume2` — RAID10 из `sdi`-`sdl`; он сохранён.

## Выполнено до создания iSCSI

- На PVE1 сохранён `/etc/pve/storage.cfg` как
  `/root/storage.cfg.pre-remove-synology-exchange-dag-20261001`.
- Удалена только пустая запись Proxmox `synology-exchange-dag`.
- RAID10 `/volume2`, NFS export и остальные storage не удалялись и не
  изменялись.

## Проверка

- После удаления `synology-exchange-dag` отсутствует в `/etc/pve/storage.cfg`.
- `pvesm status` подтверждает active-состояние всех оставшихся storage.
- PVE1/PVE2 не содержат конфигурационных ссылок на удалённый storage.

## Следующий этап

На SPB-NAS1 через DSM SAN Manager:

1. подтвердить доступность SAN Manager для конкретной модели;
2. создать отдельный iSCSI target и thick-provisioned LUN на `/volume2`;
3. ограничить target IQN PVE1/PVE2 и включить CHAP;
4. подключить LUN к PVE как block storage, провести flush/latency test;
5. для виртуальных дисков EXCH-3 использовать raw, `cache=none`,
   `virtio-scsi-single` и `iothread=1`.

На момент первичного удаления NFS DSM administrative access не был доступен;
создание target/LUN тогда было отложено. После восстановления доступа этап
выполнен ниже.

## Согласованная конфигурация iSCSI — 2026-10-01

Для временного почти двукратного объёма при перераспределении Exchange DB
создаётся один **thick-provisioned 26 TiB LUN** на `/volume2`. Это оставляет
примерно 2 TiB свободного пространства RAID10; thin provisioning и snapshots
LUN не включаются.

- target name: `PVE-EXCH3-26T`;
- target IQN: `iqn.2026-10.ru.aurora-logistics:spb-nas1-exch3`;
- LUN name: `PVE-EXCH3-26T-LUN0`;
- portal: только `10.78.5.10:3260`;
- initiator ACL, RW: только PVE1
  `iqn.1993-08.org.debian:01:fa3af0c3e152` и PVE2
  `iqn.1993-08.org.debian:01:fdd5db7a8f83`; PVE3 исключён;
- аутентификация: one-way CHAP с уникальным случайным секретом. Секрет лежит
  только в root-only `/root/synology-exch3-iscsi.chap` на SPB-NAS1, PVE1 и
  PVE2 (режим `0600`); в Git и Ansible inventory он не записывался;
- на PVE: shared iSCSI backend `content none` и обычный shared LVM VG поверх
  единственного LUN. Для EXCH-3 — только raw VM disks, `cache=none`,
  `virtio-scsi-single`, `iothread=1`; не использовать LVM-thin.

Нельзя одновременно подключать LUN к PVE1/PVE2 как обычный local LVM или
монтировать файловую систему с обоих узлов. Управление VG выполняется через
кластерный shared LVM backend Proxmox.

## Создано — 2026-10-01

- На SPB-NAS1 создан target `PVE-EXCH3-26T`, ID `1`, с IQN
  `iqn.2026-10.ru.aurora-logistics:spb-nas1-exch3`.
- One-way CHAP включён; число сессий ограничено двумя. Открытый portal
  `all:3260` удалён, оставлен только `10.78.5.10:3260`.
- Target ACL получил только initiator IQN PVE1 и PVE2 с правом RW; PVE3 не
  добавлен.
- Создан и подключён к target толстый LUN `PVE-EXCH3-26T-LUN0`, UUID
  `d4f752f6-54d2-48c7-9ae7-4cb2d8183e41`, тип `BLUN_THICK`, размер
  `28,587,302,322,176` байт (26 TiB), `/volume2`. После выделения на пуле
  осталось около 2.0 TiB свободного места (94% занято).
- На PVE1 и PVE2 выполнен CHAP login с automatic startup; устройство на обоих
  узлах — `/dev/sde`, устойчивый путь
  `/dev/disk/by-path/ip-10.78.5.10:3260-iscsi-iqn.2026-10.ru.aurora-logistics:spb-nas1-exch3-lun-1`.
- В Proxmox добавлены только для `spb-pve1,spb-pve2`:
  - iSCSI backend `synology-exch3-iscsi` (`content none`);
  - shared LVM `synology-exch3-lvm` на VG `vg_synology_exch3` (`content images`,
    `shared 1`, `saferemove 0`).
  VG создан на новом LUN и доступен с обоих PVE; свободно 26.00 TiB.

## Проверка после создания

- PVE1 и PVE2 имеют по одной сессии к target в состоянии `LOGGED_IN` через
  `10.78.5.10:3260` и видят ровно `28,587,302,322,176` байт.
- `pvesm status --storage synology-exch3-lvm` на PVE1 и PVE2: `active`,
  доступно `27,917,283,328 KiB`.
- Непосредственно после создания LUN был пуст: LV, VM-диски, файловая система
  и Exchange на нём ещё не создавались. Его последующее выделение под VM135
  отражено в следующем разделе.

## VM EXCH-3 — 2026-10-01

Клон Windows `spb-mx4` (VMID 135) находится на PVE1 и на момент настройки
остановлен. Его параметры приведены к параметрам действующих MX-серверов:

- 4 vCPU, 2 sockets, `cpu: host`, 32 GiB RAM, `balloon: 0`;
- системный `virtio0` на `synology-exch3-lvm` увеличен с 100 до 200 GiB;
- добавлены отдельные raw-LV через VirtIO SCSI single:
  - `scsi1` — 7800 GiB;
  - `scsi2` — 1700 GiB;
  - `scsi3` — 600 GiB;
  - `scsi4` — 20 GiB.

Все новые data-диски имеют `cache=none`, `iothread=1`, `discard=on`. Объёмы
повторяют текущую отдельную разметку Exchange DB на MX3 (`DB`, `DB-Murmansk`,
`DB-Krasnoyarsk`, `SystemMailboxesDB`), но не создают в госте ни разделов, ни
Exchange DB, ни путей журналов: это выполняется отдельно после утверждения
схемы баз и логов. На VG после выделения VM135 свободно 15.92 TiB.

При первом запуске VM необходимо расширить существующий раздел `C:` внутри
Windows до новых 200 GiB. VM не запускалась автоматически.

## Эксплуатационные ограничения

- У полки только один storage uplink (`eth4`/`10.78.5.10`), поэтому iSCSI
  multipath отсутствует. Высокая доступность PVE не устраняет отказ этого
  единственного кабеля/порта/NIC NAS.
- Текущий резерв пула составляет около 2 TiB. Перед созданием иных объектов
  на `/volume2` нужно учитывать, что расширять этот LUN безопасно будет
  практически некуда.

## Откат

Пока iSCSI LUN не создан, восстановить NFS storage можно из сохранённого
`storage.cfg` PVE1. Не удалять `/volume2` или RAID10: он предназначен для
будущего iSCSI LUN.

После создания, пока на LUN нет PV/VG/VM-дисков: удалить в Proxmox сначала
`synology-exch3-lvm`, затем `synology-exch3-iscsi`; деактивировать и удалить
VG/PV на PVE1, разлогинить обе PVE iSCSI-сессии, удалить target и LUN в SAN
Manager. Удаление thick LUN является разрушительной операцией и требует
повторной проверки отсутствия данных.

## Reboot/relogin

Не требуется.
