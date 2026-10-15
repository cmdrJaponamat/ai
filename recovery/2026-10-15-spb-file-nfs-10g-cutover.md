# SPB-FILE: подготовка NFS cutover на 10GbE

Дата: 2026-10-15
Статус: выполнено успешно; наблюдение после change window продолжается.

## Цель

Без перемещения raw-дисков VM135 (`SPB-MX4`) подготовить NFS-экспорт
`exchange-archive` старой полки SPB-FILE к переходу PVE на SFP storage A.

## Подтверждённые факты до изменения ACL

- PVE1 использует `10.78.4.11`, PVE2 — `10.78.4.12` в VLAN 1040.
- SPB-FILE `eth4=10.78.4.210/24`, линк 10Gb/s full duplex; `eth5=10.78.5.210/24`,
  также 10Gb/s full duplex. Это независимые пути, не bond.
- Btrfs `/volume1` и device stats healthy: ошибок чтения, записи, flush,
  corruption и generation нет.
- Экспорт `/volume1/exchange-archive` сейчас разрешает только
  `10.78.2.201` и `10.78.2.202`; поэтому read-only mount через
  `10.78.4.210` корректно получил `access denied`.
- Текущий PVE storage по-прежнему использует `10.78.2.210`; VM135 остаётся
  запущенной. Менять этот endpoint до полного preflight запрещено.

## Запланированное изменение ACL

Через DSM API `SYNO.Core.FileServ.NFS.SharePrivilege/save` полный набор
правил был заменён ровно на четыре правила с прежними параметрами:

1. сохранить `10.78.2.201` и `10.78.2.202` (`rw`, AUTH_SYS, async,
   root_squash=root);
2. добавить `10.78.4.11` и `10.78.4.12` с идентичными параметрами.

Это не переключает работающую VM и не затрагивает данные. Все четыре правила
прочитаны обратно DSM после записи.

## Результат preflight

- Прямые read-only монтирования NFSv4.1, запрошенные по `10.78.4.210`,
  успешно перечислили export на PVE1 и PVE2, но Linux распознал тот же
  NFSv4.1 server identity и применил session trunking к существующему
  transport: фактические `addr`/`clientaddr` остались `10.78.2.210` и
  `10.78.2.201/.202`. Даже `nosharecache` не изменил это поведение.
- Отдельная read-only проверка NFSv3 исключила trunking и доказала реальный
  storage A path: PVE1 `10.78.4.11 -> 10.78.4.210:2049`, PVE2
  `10.78.4.12 -> 10.78.4.210:2049`; export доступен на обоих узлах.
- Проверочные mountpoints после каждого теста штатно размонтированы и
  удалены. NFSv3 на PVE2 временно запустил `rpc-statd`; так как других
  NFSv2/v3 mount'ов нет, служба и runtime-enable сразу удалены. Состояние
  возвращено к `static/inactive`.

Следствие: storage нельзя переключать на работающей VM. В контролируемом
окне после штатной остановки VM135 нужно убрать старые NFSv4.1 mounts на
обоих PVE, убедиться, что не осталось TCP-сессий к `10.78.2.210:2049`, и
только затем подключать новый storage-id через `10.78.4.210`. До этого
нельзя менять disk references или запускать VM135.

## Выполненный cutover 2026-10-15

Владелец выбрал вариант с отдельным storage-id только для VM135.

1. Перед окном сохранены `/etc/pve/storage.cfg` и `qm config 135` на PVE1 в
   `/root/spb-file-10g-cutover-20261015-1140/`.
2. Подтверждены quorum PVE, единственный потребитель исходного storage
   (шесть raw-дисков VM135), suspended MRS requests и последняя
   application-aware Veeam-сессия: Microsoft Exchange Writer `VSS_WS_STABLE`.
3. VM135 штатно остановлена через `qm shutdown`; forced stop не применялся.
4. Старый `syno-archive-nfs` временно disabled и штатно размонтирован на
   PVE1/PVE2. До продолжения подтверждено отсутствие TCP к
   `10.78.2.210:2049`.
5. Создан `syno-archive-nfs-10g` с тем же export, `server=10.78.4.210`,
   `vers=4.1`, nodes `spb-pve1,spb-pve2`, content `images`.
6. На обоих PVE новый NFSv4.1 mount подтверждён с фактическими
   `clientaddr=10.78.4.11/.12` и `addr=10.78.4.210`.
7. Только ссылки `virtio7`–`virtio12` VM135 переведены на
   `syno-archive-nfs-10g`; volume IDs, размеры, `cache=none`, `iothread=1`,
   `backup=0`, `discard=ignore` сохранены. Данные не копировались.
8. VM135 запущена. `M:`–`R:` healthy/OK; `DB-ARCH-01`, `DB-ARCH-02` и
   `DB-FIRED-01` mounted; `MSExchangeIS`, `MSExchangeRepl`,
   `MSExchangeIMAP4BE` и `MSExchangeIMAP4` Running. Последние две службы
   пришлось повторно запустить после Windows reboot, поскольку они не
   стартуют автоматически.
9. На обоих PVE новый storage active, старый disabled; kernel journal после
   окна не содержит NFS timeout, stale-handle или RPC errors.

## Откат

Если до окончания наблюдения появятся NFS timeouts, ошибки EDB или базы
перестанут монтироваться:

1. штатно остановить VM135;
2. вернуть `qm config 135` и `storage.cfg` из
   `/root/spb-file-10g-cutover-20261015-1140/`, либо восстановить только
   шесть исходных `syno-archive-nfs:` ссылок из этого файла;
3. включить `syno-archive-nfs`, убедиться в доступности старого mount и
   только затем запустить VM135;
4. не удалять `syno-archive-nfs-10g`, export или raw-файлы до успешного
   возврата и разбора причины.

ACL старого и нового пути сохраняются параллельно. Reboot PVE/NAS не нужен.
