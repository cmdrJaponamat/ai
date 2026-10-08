# AD Sites — шаг 10: подсеть Миллионной

**Время:** 2026-10-08 10:14 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** изменение выполнено; до следующих подсетей требуется клиентская проверка VLAN 30.

## Выполненное изменение

Создано одно соответствие AD Subnet:

    New-ADReplicationSubnet -Name '192.168.203.0/24' -Site 'SITE-SPB-MILLION' -Location 'Санкт-Петербург, Миллионная, VLAN 30'

Существующие `10.78.0.0/16` → `SITE-SPB-DC` и `10.10.0.0/16` → `SITE-MMK` не менялись. Не менялись Sites, Site Links, DC placement, DNS, GPO, Exchange, PVE, маршрутизация или firewall.

## Проверка сразу после изменения

- Readback: `192.168.203.0/24` назначена `SITE-SPB-MILLION`.
- `SL-SPB-MILLION-SPB-DC` по-прежнему содержит ровно Миллионную и SITE-SPB-DC, cost 25.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям. Из SPB-DC1 сохраняется известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии без делегирования, не ошибка репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Обязательная клиентская контрольная точка

На доменном ПК с адресом `192.168.203.x` выполнить:

    nltest /dsgetsite
    nltest /dsgetdc:aurora-logistics.local /force
    gpupdate /force
    klist get krbtgt

Ожидаемый site — `SITE-SPB-MILLION`; выбранный DC — `SPB-DC1-AL` в `SITE-SPB-DC`. Затем проверить Outlook отправкой и получением тестового письма; при использовании OWA открыть его.

## Откат

Если клиентская проверка выявит проблему, удалить только новое соответствие:

    Remove-ADReplicationSubnet -Identity '192.168.203.0/24' -Confirm:$false

После отката принудительно реплицировать раздел Configuration на DC2 и повторить AD/Exchange-проверки. `SITE-SPB-MILLION` и его Site Link не менять.

## Следующий шаг

Не назначать другие подсети Миллионной до успешной клиентской проверки. Отдельно инвентаризировать сетевые сегменты, прежде чем решать, принадлежат ли они этому site.
