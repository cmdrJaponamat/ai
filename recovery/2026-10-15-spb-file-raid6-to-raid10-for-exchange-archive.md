# SPB-FILE: пересборка RAID6 в RAID10 для archive/fired

**Дата:** 2026-10-15  
**Узел:** `spb-file` / `10.78.2.210`, Synology RS2421RP+  
**Статус:** RAID10 и Btrfs-том созданы; размещение Exchange данных отложено до проверки дисков.

## Причина

Архивные базы и база уволенных ранее находились на одном шести-дисковом
RAID6/NFS SPB-FILE. При MRS и MRM это создавало неприемлемую latency/parity
нагрузку. Целевой дизайн — тот же набор шести 6-TiB HDD в RAID10 только для
`DB-ARCH-*` и `DB-FIRED-*`.

## Выполненные изменения

1. До разрушения RAID6 `DB-ARCH-01`, `DB-ARCH-02`, `DB-FIRED-01` уже были
   перенесены путями без создания новых Exchange БД на SPB-NAS1 RAID10/iSCSI:
   `J:/K:`, `Y:/Z:`, `W:/X:`. Базы оставались mounted.
2. VM135 (`SPB-MX4`) штатно остановлена. Из PVE удалены шесть старых
   NFS raw-дисков (`virtio7`–`virtio12`) и дублирующие `unused` ссылки.
   Подтверждено, что других PVE consumers старого storage нет.
3. Удалены PVE storage definitions `syno-archive-nfs` и
   `syno-archive-nfs-10g`; старые mountpoints штатно размонтированы на PVE1
   и PVE2.
4. Через DSM Storage Manager API после успешных `pre_delete_check` удалены
   единственные Btrfs volume `/volume1` и storage pool RAID6. Системные
   `md0`/`md1` не затрагивались.
5. Устаревшая missing-pool metadata удалена штатным
   `SYNO.Storage.CGI.Pool remove_missing_pool`; затем создан новый pool:

   ```sh
   synostgpool --create -t single -l raid10 \
     -d 'Exchange archive and fired RAID10' \
     /dev/sata1 /dev/sata2 /dev/sata3 /dev/sata4 /dev/sata5 /dev/sata6
   ```

6. На `/dev/md2` создан единственный Btrfs `/volume1`, `relatime`, без
   dedupe, через `SYNO.Storage.CGI.Volume deploy_unused`.
7. VM135 запущена обратно. Все три базы смонтированы, Exchange IS, FastSearch,
   HostController и MRS работают; MX4 не использует SPB-FILE.

## Проверка

- `/proc/mdstat`: `md2 : active raid10`, `[6/6] [UUUUUU]`.
- Размер Btrfs `/volume1`: около 16 TiB usable, занято около 82 MiB.
- Все шесть HDD `normal`; система RAID1 `md0`/`md1` сохранилась.
- `DB-ARCH-01`, `DB-ARCH-02`, `DB-FIRED-01`: `Mounted=True` по новым путям
  SPB-NAS1.
- DSM пока показывает `has_unverified_disk`. Это не degraded RAID, но
  является стоп-условием для размещения данных до отдельной проверки дисков.

## Откат

Отката к прежнему RAID6 и его данным нет: он намеренно разрушен с согласия
владельца после вывода всех его потребителей. Рабочие базы остаются на
SPB-NAS1 RAID10; восстановление при отказе — из их текущих копий/Veeam.

## Следующие шаги

1. Выполнить и подтвердить DSM disk verification/SMART для всех шести HDD,
   дождаться исчезновения `has_unverified_disk`.
2. Создать на `/volume1` новый export для PVE1/PVE2 по SFP storage-путям,
   с новым storage-id (не восстанавливать старые definitions).
3. Создать новые virtual disks и переносить archive/fired последовательно,
   с application-aware backup и проверкой mount после каждой БД.

Reboot NAS и PVE не требуется. Перезапуск MX4 уже выполнен штатно.
