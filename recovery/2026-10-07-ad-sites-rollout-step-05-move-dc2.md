# AD Sites — шаг 5: перенос DC2 в SITE-MMK

**Время:** 2026-10-07 17:41 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** изменение выполнено; ожидается контрольное подтверждение на самом DC2 до следующего шага.

## Выполненное изменение

Перемещён только объект сервера контроллера домена `dc2` в AD Site `SITE-MMK`:

```powershell
Move-ADDirectoryServer -Identity 'dc2' -Site 'SITE-MMK'
```

Подсети AD не создавались и не назначались. DNS, GPO, Exchange, PVE, маршрутизация и firewall не менялись.

## Немедленная проверка с SPB-DC1

- `DC2.aurora-logistics.local` (`10.10.20.50`) отображается в `SITE-MMK`, является GC.
- `spb-dc1-al.aurora-logistics.local` (`10.78.3.50`) остаётся в `SITE-SPB-DC`, является GC.
- `SL-AD-TRANSITION` включает Default-First-Site-Name, SITE-SPB-DC и SITE-MMK; cost 100, интервал 15 минут.
- `repadmin /replsummary`: 0 ошибок у доступных направлений. Со стороны SPB-DC1 остаётся известное `110 - DC2` при удалённом опросе DC2 текущей SSH-сессией без делегированных учётных данных; это не ошибка репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0--1. Одиночная `Mailbox Database 1610298417` остаётся mounted на SPB-MX4 как исходно известное исключение.

## Обязательная контрольная точка

На DC2 выполнить:

```powershell
Get-ADDomainController -Identity dc2 |
  Select-Object HostName,IPv4Address,Site,IsGlobalCatalog
repadmin /replsummary
```

Ожидаемый Site — `SITE-MMK`, ошибок репликации — 0. До этого подтверждения не создавать AD Subnet.

## Откат

Если подтверждение или сервисные проверки выявят проблему:

```powershell
Move-ADDirectoryServer -Identity 'dc2' -Site 'Default-First-Site-Name'
```

После отката повторить команды контрольной точки и проверить DAG.

## Следующий шаг

Только после успешной контрольной точки: отдельным изменением создать одно соответствие `10.78.0.0/16` → `SITE-SPB-DC`, затем проверить AD и почту на канарейном клиенте. `10.10.0.0/16` в этом изменении не добавлять.
