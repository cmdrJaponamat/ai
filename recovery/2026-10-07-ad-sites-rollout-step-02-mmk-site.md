# AD Sites rollout — шаг 2: пустой SITE-MMK

**Время:** 2026-10-07 16:39 MSK
**Статус:** выполнен, контролируемый

## Изменение

На `spb-dc1-al` создан только объект AD Site `SITE-MMK`.

После шага существуют `Default-First-Site-Name`, `SITE-SPB-DC` и `SITE-MMK`.
Subnet-объекты, Site Links и размещение DC не менялись.

## Проверка после изменения

- Число AD Subnet равно 0.
- Оба DC остаются в `Default-First-Site-Name`.
- По-прежнему существует только `DEFAULTIPSITELINK`, cost 100, interval
  180 минут.
- `repadmin /replsummary`: 0 failures из 5 в обоих направлениях; известный
  diagnostic error 110 для DC2 не изменился.
- На MX4 все пассивные копии Healthy, активная однокопийная база Mounted;
  copy-очереди нулевые.

## Откат

До создания Site Link, subnet и переноса DC:

```powershell
Remove-ADReplicationSite -Identity 'SITE-MMK' -Confirm:$false
```

## Следующий шаг

Создать `SL-AD-TRANSITION` с Sites `Default-First-Site-Name`,
`SITE-SPB-DC`, `SITE-MMK`, cost 100, интервалом 15 минут и расписанием 24×7.
