# AD Sites rollout — шаг 4: перенос SPB-DC1-AL

**Время:** 2026-10-07 17:21 MSK
**Статус:** выполнен, контролируемый

## Изменение

Объект контроллера `spb-dc1-al` перенесён из `Default-First-Site-Name` в
`SITE-SPB-DC`.

`dc2` остаётся в `Default-First-Site-Name`; AD Subnet-объекты по-прежнему не
созданы. IP-адреса, DNS, SYSVOL, NETLOGON, Exchange/DAG, маршрутизация и GPO
не изменялись.

## Проверка после изменения

- `spb-dc1-al` (`10.78.3.50`) — `SITE-SPB-DC`, Global Catalog.
- `dc2` (`10.10.20.50`) — `Default-First-Site-Name`, Global Catalog.
- `SL-AD-TRANSITION` содержит все три Site, cost 100, interval 15 минут.
- `repadmin /replsummary`: 0 failures из 5 в обоих направлениях;
  диагностический error 110 для DC2 сохраняется без изменения.
- `dcdiag` Advertising/SYSVOL/DNS без ошибок.
- DAG02 operational на SPB-MX3 и SPB-MX4; все пассивные копии на MX4 Healthy,
  copy-очереди 0, активная однокопийная база Mounted.

## Контрольная точка

До переноса `dc2` требуется подтвердить на самом DC2, что
`Get-ADDomainController -Identity spb-dc1-al` возвращает
`Site = SITE-SPB-DC`. Это доказывает репликацию переноса DC в Мурманск до
следующего необратимого шага.

## Откат

```powershell
Move-ADDirectoryServer -Identity 'spb-dc1-al' -Site 'Default-First-Site-Name'
```

После отката повторить `repadmin /replsummary` и `dcdiag`.

## Следующий шаг

После подтверждения на DC2 переместить `dc2` в `SITE-MMK`; subnet пока не
создавать.
