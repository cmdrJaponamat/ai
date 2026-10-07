# Veeam: резервное копирование Exchange DAG02

**Дата:** 2026-10-07  
**Сервер Veeam:** VM 131 `spb-veeam` на PVE2  
**Репозиторий:** `storage-on-pbs`, `10.78.3.178:/mnt/pbs-backups/veeam-backups`

## Исходная политика PBS для MX3

Для VM 117 `spb-mx3` найдено отдельное задание PBS:

- снимок VM: вт/чт/сб в 00:05 МСК;
- pruning: `keep-last=7`, `keep-weekly=2`, `keep-monthly=1`;
- target: `pbs-backup`;
- ограничение пропускной способности: 400 MiB/s.

PBS хранит образы VM, однако не выполняет Exchange application-aware
обработку. Поэтому его снимок не заменяет VSS-резервную копию баз Exchange.

## Созданная защита Exchange

Создана отдельная Veeam protection group `Exchange DAG02`:

- узлы: `SPB-MX3` и `SPB-MX4`;
- учётные данные развёртывания: существующие сохранённые
  `aurora-logistic\\veeam`;
- Veeam Agent будет автоматически установлен/обновлён при первом запуске без
  разрешения на автоматическую перезагрузку;
- группа не использует бывший MX2.

Создано и включено задание `bkp_exchange_dag02`:

| Параметр | Значение |
| --- | --- |
| Охват | оба узла `DAG02` |
| Томы | `E:`, `F:`, `G:`, `H:` |
| Консистентность | application-aware processing, Exchange VSS |
| Журналы Exchange | `ProcessLogsWithJob`; обрезаются только после успешной резервной копии |
| Репозиторий | `storage-on-pbs` |
| Расписание | вт/чт/сб, 06:00 МСК |
| Повтор при ошибке | 3 попытки, интервал 10 минут |
| Короткое хранение | 7 restore points |
| GFS | 2 weekly, 1 monthly |

Время 06:00 намеренно отстоит от PBS-снимка MX3 в 00:05. Частота и retention
совпадают с PBS.

`C:` из задания Veeam исключён намеренно: Veeam отвечает только за тома баз и
журналов Exchange, а образ операционной системы и Exchange binaries сохраняет
PBS. Все тома с базами и журналами (`E:`--`H:`) остались в одном
application-aware задании, поэтому условия VSS для согласованности и очистки
журналов Exchange сохраняются.

## Корректировка PBS

На PVE1 для обеих почтовых VM data-диски помечены `backup=0`:

| VM | Системный диск, остаётся в PBS | Исключено из PBS |
| --- | --- | --- |
| `117` SPB-MX3 | `scsi0`, 200 GiB (`C:`) | `scsi1`, `scsi2`, `virtio0`, `virtio1` (`E:`--`H:`) |
| `135` SPB-MX4 | `virtio0`, 200 GiB (`C:`) | `virtio1`--`virtio4` (`E:`--`H:`) |

Отдельное PBS-задание для VM135 создано с retention, идентичным MX3:

- target `pbs-backup`, snapshot mode, лимит 400 MiB/s;
- вт/чт/сб в 00:35 МСК;
- `keep-last=7`, `keep-weekly=2`, `keep-monthly=1`;
- уведомления о сбое: `it@aurora-logistics.ru`.

MX3 сохраняет существующее PBS-задание вт/чт/сб в 00:05 МСК с тем же
retention. Таким образом PBS больше не хранит копии Exchange-баз, а покрывает
только восстановление ОС/Exchange VM; Veeam хранит только базы и журналы.

## Проверка

- Veeam repository имеет 45,7 TiB свободного места на момент настройки.
- `bkp_exchange_dag02`: `JobEnabled=True`, `ScheduleEnabled=True`,
  `ApplicationProcessingEnabled=True`, `GFSRetentionEnabled=True`.
- В задание включены именно `E:`, `F:`, `G:`, `H:`; `OS Volume` отсутствует.
- Старые задания `bkp_exchange_volumes` и `bkp_exchange_entire_vm` на
  бывший адрес MX2 `10.78.3.60` сохранены выключенными и не менялись.

Первый запуск будет полным и прочитает примерно 15 TiB фактически занятых
данных двух серверов; его длительность и влияние на хранилище нужно наблюдать.

## Откат

Отключить только новое расписание, не трогая старые задания:

```powershell
Get-VBRComputerBackupJob -Name 'bkp_exchange_dag02' |
  Disable-VBRComputerBackupJob
```

Полностью удалить новое задание и protection group можно только после
подтверждения, что первая сессия не требуется для расследования:

```powershell
Get-VBRComputerBackupJob -Name 'bkp_exchange_dag02' |
  Remove-VBRComputerBackupJob
Get-VBRProtectionGroup -Name 'Exchange DAG02' |
  Remove-VBRProtectionGroup
```

Для возврата к полному PBS-бэкапу на PVE1 удалить `backup=0` из перечисленных
disk-параметров VM117/VM135. Исходные конфигурации сохранены на PVE1:
`/root/117.conf.pre-pbs-system-only-20261007` и
`/root/135.conf.pre-pbs-system-only-20261007`.
