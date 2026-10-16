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
- При двух параллельных MRS-переносах в `DB-FIRED-01` оба запроса вошли в
  `StalledDueToTarget_DiskLatency` с нулевой текущей скоростью. Во время
  нагрузки на RAID10 измерены задержки записи отдельных HDD до 48–91 ms;
  CPU NAS и 10GbE-канал не были насыщены. По разрешению владельца для
  изоляции нагрузки у заявки Аксянова запрошено приостановление
  (`Suspend=True`); MRS ещё должен применить это в очередном цикле.
- По следующему явному решению владельца `DB-FIRED-01` возвращена на
  SPB-NAS1: созданы новые VM135 `virtio9/10` на `synology-exch3-lvm`
  (900/150 GiB), в Windows это W:/X: (GPT, NTFS, 4 KiB). После штатного
  dismount EDB и журналы скопированы M:/N: -> W:/X:, проверено побайтное
  равенство EDB `18,924,699,648` и журналов `20,305,682,432`; конфигурация
  базы переключена только `Move-DatabasePath -ConfigurationOnly` на
  `W:\DB-FIRED-01\DB-FIRED-01.edb` / `X:\DB-FIRED-01\Logs`. База mounted.
- M:/N: на SPB-FILE и PVE `virtio7/8` намеренно пока сохранены как откатная
  копия. Не удалять, не форматировать и не применять к ним новую нагрузку до
  свежего application-aware Veeam backup и отдельного решения о дальнейшей
  роли SPB-FILE.

## Откат

Отката к прежнему RAID6 и его данным нет: он намеренно разрушен с согласия
владельца после вывода всех его потребителей. Для текущего возврата fired
откат до отдельного решения доступен: штатно размонтировать `DB-FIRED-01`,
переключить пути ConfigurationOnly обратно на M:/N: и смонтировать. Основной
вариант восстановления при отказе остаётся Veeam.

## Следующие шаги

1. Обновить scope задания Veeam для MX4: включить текущие W:/X: и исключить
   бывшие M:/N: только после отдельной проверки задачи; затем дождаться
   успешной свежей application-aware точки для `DB-FIRED-01` на NAS1.
2. `DB-ARCH-01` и `DB-ARCH-02` оставить на SPB-NAS1 (`J:/K:`, `Y:/Z:`) до
   отдельного решения и окна. На новую полку их не переносить автоматически.
3. До проверки производительности не возобновлять MRS. После отдельного
   решения возобновить только одну заявку и измерить её скорость на NAS1.

## MRS после возврата на NAS1

- По следующему разрешению возобновлена только заявка Мсоева; заявка Аксянова
  осталась с `Suspend=True`.
- Для сброса устаревшего статуса `Target_DiskLatency` перезапущен MRS на MX4.
  Штатная остановка зависла, поэтому завершён только PID MRS и служба сразу
  штатно запущена. MRS на исходном MX3 также штатно stop/start после нового
  статуса `StalledDueToSource_MailboxCapacityExceeded`. Information Store,
  транспорт, базы и серверы не перезапускались.
- После этого Мсоев перешёл в `CopyingMessages`: 43%, 8.208 GiB,
  217.9 MB/min (~3.63 MB/s). Это близко к ранее наблюдавшимся 235.9 MB/min
  (~3.93 MB/s), но не является ростом скорости; зато целевая disk-latency
  больше не останавливает заявку.

Reboot NAS и PVE не требуется. Перезапуск MX4 уже выполнен штатно.

## Аварийное заполнение журнала DB-FIRED-01, 2026-10-16

- После массового запуска MRS `X:` (150 GiB) заполнился: 0 GiB свободно,
  149.7 GiB журналов и 153 294 файла. `DB-FIRED-01` размонтировалась;
  `Suspend-MoveRequest` во время offline закономерно вернул
  `MailboxOfflineException`.
- Причина: Veeam scope оставался на прежних M:/N: и не включал новый X:,
  поэтому application-aware backup не мог усечь журналы DB-FIRED-01.
- Для сохранения всех журналов, без circular logging и без удаления файлов,
  PVE-диск VM135 `virtio10` на SPB-NAS1 увеличен 150 -> 300 GiB; GPT/NTFS X:
  расширен online. Exchange успешно выполнил recovery и mounted базу.
  После расширения свободно около 150 GiB.
- Все 23 MoveRequest получили `Suspend=True`. Их не возобновлять до
  успешной application-aware Veeam-точки со scope `J:, K:, Y:, Z:, W:, X:`.
