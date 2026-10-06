# Срез Exchange DAG перед внедрением AD Sites — 2026-10-06

## Назначение и способ сбора

Read-only срез выполнен 2026-10-06 около 10:25 MSK для решения о допустимости
параллельного внедрения AD Sites и полной репликации Exchange-баз. Данные
сняты на `SPB-MX4` (VMID 135, `10.78.3.63`) через QEMU Guest Agent с PVE1:
внешний `sshd` на MX4 остановлен (`Manual`), TCP/22 не слушает. Конфигурация
Exchange, Windows, PVE, сети и AD не изменялась.

## Топология и базовое состояние

- DAG: `DAG02`.
- Участники и operational members: `SPB-MX2`, `SPB-MX3`, `SPB-MX4`.
- Witness: `spb-wts-al.aurora-logistics.local`, `C:\DAGWitness`.
- Cluster node state: все три узла `Up`.
- На MX4 службы `ClusSvc`, `MSExchangeDagMgmt`, `MSExchangeIS` и
  `MSExchangeRepl` — `Running`, `Automatic`.
- На MX4 политика автоматической активации копий — `Blocked`; на MX2 и MX3 —
  `Unrestricted`. Это соответствует подготовке нового участника и не должно
  сниматься до отдельного решения после завершения проверок.

## Состояние копий на момент среза

| База / копия | Состояние | Очереди | Вывод |
| --- | --- | --- | --- |
| `Admins\SPB-MX2` | `Mounted` | 0 / 0 | активная копия |
| `Admins\SPB-MX3`, `Admins\SPB-MX4` | `Healthy` | 0 / 0 | две здоровые пассивные копии |
| `fired\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `fired\SPB-MX2` | `Healthy` | 0 / 0 | здоровая пассивная копия |
| `kras\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `kras\SPB-MX2` | `FailedAndSuspended` | 15 286 / 4 | сообщение Exchange указывает на inconsistency/corruption от 07.09.2026; необходим отдельный full reseed |
| `Krasnoyarsk\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `Krasnoyarsk\SPB-MX2` | `FailedAndSuspended` | 376 094 / 105 | incremental seeding не завершён; Exchange требует full reseed |
| `Mailbox Database 1610298417\SPB-MX4` | `Mounted` | 0 / 0 | единственная наблюдаемая копия; не имеет требуемой избыточности |
| `MailBoxDB_AL_new\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `MailBoxDB_AL_new\SPB-MX4` | `Healthy` | 0 / 1 | здоровая пассивная копия |
| `MailBoxDB_AL_new\SPB-MX2` | `FailedAndSuspended` | 688 567 / 2 | серьёзная I/O-ошибка, зафиксированная 22.08.2026; требуется отдельное решение о reseed/восстановлении |
| `mmk\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `mmk\SPB-MX4` | `Seeding` | 1 568 794 / 0 | идёт полный seed; на момент health-check длительность около 49 минут |
| `mmk\SPB-MX2` | `FailedAndSuspended` | 128 138 / 435 | inconsistency/corruption от 16.07.2026; копия автоматически suspended |
| `spb-mdb2\SPB-MX2` | `Mounted` | 0 / 0 | активная копия |
| `spb-mdb2\SPB-MX3` | `Healthy` | 0 / 0 | здоровая пассивная копия |
| `spb-mdb3\SPB-MX3` | `Mounted` | 0 / 0 | наблюдаемая активная копия |
| `SystemMailboxesDB\SPB-MX3` | `Mounted` | 0 / 0 | активная копия |
| `SystemMailboxesDB\SPB-MX2`, `SystemMailboxesDB\SPB-MX4` | `Healthy` | 0 / 0 | здоровые пассивные копии |

## Health-check

`Test-ReplicationHealth -Identity SPB-MX4` успешно прошёл проверки
ActiveManager, ClusterNetwork, ClusterService, DagMembersUp,
DBLogCopyKeepingUp, DBLogReplayKeepingUp, MonitoringService, QuorumGroup,
ReplayService, ServerLocatorService, TasksRpcListener и TcpListener.

Проверки `DatabaseAvailability` и `DatabaseRedundancy` ожидаемо не прошли:

- `Mailbox Database 1610298417` имеет только одну копию;
- `mmk\SPB-MX4` ещё находится в `Seeding`, а копия на MX2 failed;
- failed-копии на MX2 снижают избыточность соответствующих баз;
- MX4 намеренно имеет `DatabaseCopyAutoActivationPolicy=Blocked`.

## Вывод для AD Sites

До окончания full seed `mmk\SPB-MX4`, проверки его перехода в `Healthy` и
отдельного решения по failed/suspended копиям MX2 не менять AD Sites, subnet
mapping, расположение DC или Site Links. Разрешена только read-only подготовка
и документирование: сейчас Exchange не имеет достаточной избыточности для
одновременного изменения другой критичной инфраструктуры.

## Следующий read-only контроль

Снять повторно:

```powershell
Get-MailboxDatabaseCopyStatus * |
  Format-Table Name,Status,CopyQueueLength,ReplayQueueLength,ErrorMessage -Auto
Test-ReplicationHealth -Identity SPB-MX4
Get-DatabaseAvailabilityGroup -Status
```

Критерий завершения именно текущего этапа: `mmk\SPB-MX4` становится `Healthy`
с устойчиво нулевыми очередями. Это не означает автоматическое устранение
старых failed/suspended копий MX2: они требуют отдельного change-plan.
