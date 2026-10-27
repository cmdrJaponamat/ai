# Снижение дисковой нагрузки Veeam на Exchange DAG02

Дата: 2026-10-27 (MSK)  
Объект: Veeam protection group `Exchange DAG02`, SPB-MX3/MX4.

## Причина

Во время ежедневного `bkp_exchange_dag02` Zabbix фиксировал кратковременные
высокие queue/latency на обоих Exchange-узлах. История за 90 дней показала,
что события возникают только в окнах backup. Последняя сессия шла 03:30–09:37
MSK: MX3 читался 03:32–06:06, MX4 — 06:09–09:37. Каждый узел прочитал около
7.3 TiB; средняя скорость чтения была 835 и 608 MiB/s соответственно.

## Изменение

В Veeam protection group `Exchange DAG02` включён штатный Veeam Agent Backup
I/O throttling для `Servers`:

- `EnableAgentThrottling=True`;
- `ThrottleAgentOn=Servers`;
- network bandwidth throttling намеренно не включался.

До изменения throttling уже был включён, но применялся только к
`Workstations`, поэтому на MX3/MX4 не действовал. Veeam Agent по новой
политике понижает приоритет backup-активности, когда сервер занят. Это может
увеличить длительность job, но должно снизить задержки I/O Exchange.

## Проверка

- Readback Veeam подтвердил `Throttle on Servers only`.
- На MX3 и MX4 работают `VeeamEndpointBackupSvc`, `VeeamTransportSvc` и
  `VeeamDeploySvc`.
- Restart/reboot Exchange, Veeam или VM не выполнялись.
- Managed policy доставляется агентам при штатном rescan/следующем запуске
  задания; результат необходимо сравнить по следующей сессии с Zabbix
  (p95/max queue и write latency) и длительностью Veeam.

## Откат

В Veeam изменить Advanced Windows options protection group `Exchange DAG02`
на `Do not throttle agent` либо вернуть `ThrottleAgentOn=Workstations`.
Это не влияет на VSS, application-aware processing, состав томов или
усечение Exchange logs.
