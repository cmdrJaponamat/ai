# AD Sites — шаг 11: временная привязка московского агрегата

**Время:** 2026-10-08 11:02 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** изменение выполнено; обязательна проверка с доступного клиента `10.77.3.40`.

## Выполненное изменение

Создано одно временное соответствие:

    New-ADReplicationSubnet -Name '10.77.0.0/16' -Site 'SITE-SPB-DC' -Location 'Временно: Москва; SITE-MSK-OFFICE ещё не создан'

Причина: `10.77.3.40` ранее возвращал `ERROR_NO_SITENAME`; физический site Москвы известен, но `SITE-MSK-OFFICE` ещё не создан. По утверждённому правилу неописанный/не имеющий созданного site агрегат временно относится к `SITE-SPB-DC` до последующего переназначения существующего объекта.

Не менялись другие AD Subnet, Sites, Site Links, размещение DC, DNS, GPO, Exchange, PVE, маршрутизация или firewall.

## Проверка после изменения

- Readback: `10.77.0.0/16` → `SITE-SPB-DC`.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям; известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии SPB-DC1 не является ошибкой репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Контрольная точка

На доменном клиенте `10.77.3.40` выполнить:

    nltest /dsgetsite
    nltest /dsgetdc:aurora-logistics.local /force
    gpupdate /force
    klist get krbtgt

Ожидаемый site и выбранный DC: `SITE-SPB-DC` / `SPB-DC1-AL`.

## Откат

Если клиентская проверка выявит проблему:

    Remove-ADReplicationSubnet -Identity '10.77.0.0/16' -Confirm:$false

После отката повторить AD и Exchange-проверки.

## Следующий шаг

После подтверждения клиентом по одному CIDR применять утверждённое правило: сети с уже созданным целевым site назначать ему, остальные подтверждённые физические сети временно относить к `SITE-SPB-DC`; VPN, транзитные, guest и конфликтующие пулы не добавлять.
