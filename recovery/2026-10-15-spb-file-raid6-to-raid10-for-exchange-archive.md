# SPB-FILE: пересборка RAID6 в RAID10 для archive/fired

**Дата:** 2026-10-15  
**Узел:** `spb-file` / `10.78.2.210`, Synology RS2421RP+  
**Статус:** RAID10 и Btrfs-том созданы; `DB-FIRED-01` размещена на новой
полке. Архивные базы остаются на SPB-NAS1.

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
8. Владелец явно принял риск статуса DSM `has_unverified_disk` как следствие
   давно используемых несертифицированных Synology HDD, а не как признак
   деградации. Создан отдельный DSM share `/volume1/exchange-fired-r10` и
   export NFSv4.1 только для `10.78.4.11` и `10.78.4.12`; на PVE создан
   отдельный storage-id `spb-file-fired-r10` (`10.78.4.210`).
9. Для VM135 созданы только два новых raw-диска на этом storage (`virtio7`
   900 GiB и `virtio8` 150 GiB, `cache=none`, `iothread=1`, `backup=0`,
   `discard=ignore`). В Windows это `M:` и `N:`, NTFS/4 KiB.
10. `DB-FIRED-01` штатно размонтирована, EDB и журналы скопированы из
    временных `W:/X:`. До mount проверено равенство EDB
    `17,314,086,912` байт и журнала; путь переключён только через
    `Move-DatabasePath -ConfigurationOnly`. База успешно mounted на
    `M:\DB-FIRED-01\DB-FIRED-01.edb` / `N:\DB-FIRED-01\Logs`.

## Проверка

- `/proc/mdstat`: `md2 : active raid10`, `[6/6] [UUUUUU]`.
- Размер Btrfs `/volume1`: около 16 TiB usable, занято около 82 MiB.
- Все шесть HDD `normal`; система RAID1 `md0`/`md1` сохранилась.
- `DB-ARCH-01`, `DB-ARCH-02`, `DB-FIRED-01`: `Mounted=True` по новым путям
  SPB-NAS1.
- DSM показывает `has_unverified_disk`; RAID при этом не degraded. Владелец
  принял этот риск как ожидаемое предупреждение о несертифицированных HDD.
- `DB-FIRED-01` mounted на новой RAID10 полке. После mount появились два
  штатных новых Exchange log-файла, поэтому целевой каталог журналов больше
  исходного на 1,212,416 байт.
- По явному решению владельца временные `W:/X:` признаны невалидными после
  переключения пути. Их Windows-диски 11/12, PVE `scsi5/scsi6` и LVM тома
  `vm-135-disk-11`/`vm-135-disk-12` удалены. Отката на SPB-NAS1 больше нет.

## Откат

Отката к прежнему RAID6 и его данным нет: он намеренно разрушен с согласия
владельца после вывода всех его потребителей. Рабочие базы остаются на
SPB-NAS1 RAID10; восстановление при отказе — из их текущих копий/Veeam.

## Следующие шаги

1. Дождаться успешной свежей application-aware Veeam-точки для MX4 с уже
   новым путём `DB-FIRED-01`.
2. `DB-ARCH-01` и `DB-ARCH-02` оставить на SPB-NAS1 (`J:/K:`, `Y:/Z:`) до
   отдельного решения и окна. На новую полку их не переносить автоматически.

Reboot NAS и PVE не требуется. Перезапуск MX4 уже выполнен штатно.
