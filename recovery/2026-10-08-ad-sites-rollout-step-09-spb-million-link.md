# AD Sites — шаг 9: топологический link Миллионная ↔ ЦОД СПБ

**Время:** 2026-10-08 10:11 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** выполнено; клиентский выбор DC не изменён до назначения подсети.

## Выполненное изменение

Создан один AD Site Link:

    New-ADReplicationSiteLink -Name 'SL-SPB-MILLION-SPB-DC' -SitesIncluded 'SITE-SPB-MILLION','SITE-SPB-DC' -Cost 25

В link включены только `SITE-SPB-MILLION` и `SITE-SPB-DC`. Переходный `SL-AD-TRANSITION` не менялся. Никакая AD Subnet, DC placement, DNS, GPO, Exchange, PVE, маршрутизация или firewall не менялись.

## Семантика

На Миллионной нет DC, поэтому link не вызывает межсайтовую AD-репликацию. Его текущая задача — задать для DC Locator путь с меньшей стоимостью к `SITE-SPB-DC`, чем к `SITE-MMK`, когда впоследствии будет назначена клиентская подсеть `192.168.203.0/24`.

Атрибут `replInterval` не задан на объекте (readback пуст). Пока в `SITE-SPB-MILLION` нет DC, это не влияет на трафик или сервис. Перед будущим повышением DC на площадке отдельным изменением задать согласованный интервал и расписание репликации.

## Проверка после изменения

- Link содержит ровно `SITE-SPB-MILLION` и `SITE-SPB-DC`, cost `25`.
- Подсеть Миллионной не назначена; существуют только `10.78.0.0/16` → `SITE-SPB-DC` и `10.10.0.0/16` → `SITE-MMK`.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям; известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии SPB-DC1 не является ошибкой репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как исходно известное исключение.

## Откат

Пока link не имеет DC или назначенной подсети, точечный откат:

    Remove-ADReplicationSiteLink -Identity 'SL-SPB-MILLION-SPB-DC' -Confirm:$false

После отката повторить `repadmin /replsummary` и `dcdiag`. Не менять `SL-AD-TRANSITION`.

## Следующий шаг

Только отдельным изменением назначить `192.168.203.0/24` → `SITE-SPB-MILLION`, затем проверить DC Locator, GPO, Kerberos и Outlook с доменного клиента Миллионной.
