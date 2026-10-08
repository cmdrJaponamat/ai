# AD Sites — шаг 13: создание недостающих пустых sites

**Время:** 2026-10-08 11:22 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** выполнено; все созданные sites пусты и не влияют на выбор DC до отдельного переназначения subnet.

## Выполненное изменение

Созданы только следующие AD Site:

- `SITE-SPB-REMESLENNAYA`
- `SITE-MSK-OFFICE`
- `SITE-KRR`
- `SITE-NU`
- `SITE-UST-KUT`
- `SITE-VITIM2`
- `SITE-YASTREB`

Не менялись AD Subnet, Site Links, размещение DC, DNS, GPO, Exchange, PVE, маршрутизация и firewall.

## Проверка после изменения

- В AD теперь 11 Site: Default-First-Site-Name и 10 целевых sites.
- Все 22 AD Subnet сохраняют прежнее распределение: `SITE-SPB-DC` 14, `SITE-MMK` 6, `SITE-SPB-MILLION` 2. Ни одна сеть не назначена новому site.
- Существуют только прежние Site Links: DEFAULTIPSITELINK, SL-AD-TRANSITION и SL-SPB-MILLION-SPB-DC.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям; известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии SPB-DC1 не является ошибкой репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Откат

Каждый site пока пуст и не имеет Site Link. При необходимости удалить только конкретный ошибочно созданный объект:

    Remove-ADReplicationSite -Identity '<SITE-NAME>' -Confirm:$false

Перед удалением убедиться, что в site нет subnet, DC и Site Link.

## Следующий шаг

Создавать Site Link и переносить subnet к каждому из новых sites отдельными контролируемыми шагами, после подтверждения физической сети и клиентской проверки. Нельзя переносить все временные подсети массово.
