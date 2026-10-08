# AD Sites — шаг 8: пустой Site Миллионной

**Время:** 2026-10-08 10:02 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** выполнено; site не влияет на клиентов до отдельного создания Site Link и назначения подсети.

## Выполненное изменение

Создан ровно один пустой объект AD Site:

    New-ADReplicationSite -Name 'SITE-SPB-MILLION'

Ни одна AD Subnet не назначалась. Не изменялись Site Links, размещение DC, DNS, GPO, Exchange, PVE, маршрутизация или firewall.

## Обоснование

Read-only проверка маршрутизатора `AL-SPB-MILLION` подтверждает локальную сеть площадки VLAN 30 `192.168.203.0/24` и активный маршрут `10.78.0.0/16` через `WG-SPB-DC`. До `SPB-DC1-AL` (`10.78.3.50`) 5/5 ICMP без потерь, средняя задержка 4.8 мс. Это обосновывает отдельный site с предпочтением `SITE-SPB-DC`, но не требует размещения DC на Миллионной.

## Проверка после изменения

- `SITE-SPB-MILLION` существует и пуст: в нём нет серверов/подсетей.
- Существуют только `10.78.0.0/16` → `SITE-SPB-DC` и `10.10.0.0/16` → `SITE-MMK`.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям; ограничение опроса DC2 (`110`) из SSH-сессии SPB-DC1 остаётся известным ограничением делегированных учётных данных, не ошибкой репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Откат

Поскольку Site пуст и не связан с Site Link, DC или AD Subnet, точечный откат:

    Remove-ADReplicationSite -Identity 'SITE-SPB-MILLION' -Confirm:$false

После отката повторить `repadmin /replsummary` и `dcdiag`.

## Следующий шаг

Отдельным изменением создать `SITE-SPB-MILLION ↔ SITE-SPB-DC` Site Link (cost 25, репликация 15 минут, 24x7), не меняя переходный `SL-AD-TRANSITION`. Только после проверки этого link назначить `192.168.203.0/24` новому site.
