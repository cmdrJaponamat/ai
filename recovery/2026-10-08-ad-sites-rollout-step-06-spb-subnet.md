# AD Sites — шаг 6: привязка сети Санкт-Петербурга

**Время:** 2026-10-08 09:25 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** изменение выполнено; до следующего шага нужна клиентская проверка.

## Выполненное изменение

Создано единственное соответствие AD Subnet:

```powershell
New-ADReplicationSubnet -Name '10.78.0.0/16' \
  -Site 'SITE-SPB-DC' \
  -Location 'Санкт-Петербург, ЦОД и сервисная сеть'
```

`10.10.0.0/16` и другие подсети не изменялись. Не менялись Sites, Site Links, DC placement, DNS, GPO, Exchange, PVE, маршрутизация и firewall.

## Проверка сразу после изменения

- Readback: `10.78.0.0/16` назначена `SITE-SPB-DC`.
- DC placement: `SPB-DC1-AL` в `SITE-SPB-DC`, `DC2` в `SITE-MMK`; оба GC.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям. Из SPB-DC1 сохраняется известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии без делегирования; это не ошибка репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Обязательная клиентская контрольная точка

На одном рабочем ПК с адресом `10.78.x.x` выполнить:

```cmd
nltest /dsgetsite
nltest /dsgetdc:aurora-logistics.local
gpupdate /force
klist get krbtgt
```

Ожидаемый сайт — `SITE-SPB-DC`, DC — `SPB-DC1-AL` или иной доступный доменный контроллер согласно locator. После команд проверить вход в Outlook и отправку/приём одного тестового сообщения; при наличии OWA — открыть его.

## Откат

Если клиентская проверка выявит проблему, удалить только созданное соответствие:

```powershell
Remove-ADReplicationSubnet -Identity '10.78.0.0/16' -Confirm:$false
```

Затем принудительно реплицировать раздел Configuration на DC2 и повторить AD/Exchange проверки. Sites и DC placement при этом не менять.

## Следующий шаг

Только после успешной клиентской проверки отдельным изменением рассмотреть `10.10.0.0/16` → `SITE-MMK`.
