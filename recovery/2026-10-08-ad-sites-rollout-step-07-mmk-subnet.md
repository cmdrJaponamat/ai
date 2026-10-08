# AD Sites — шаг 7: привязка сети Мурманска

**Время:** 2026-10-08 09:34 MSK
**Система:** Active Directory `aurora-logistics.local`
**Статус:** изменение выполнено; до новых подсетей нужны проверки на DC2 и клиенте `10.10.x.x`.

## Выполненное изменение

Создано одно соответствие AD Subnet:

    New-ADReplicationSubnet -Name '10.10.0.0/16' -Site 'SITE-MMK' -Location 'Мурманск и территориальные площадки'

Единственное ранее созданное соответствие `10.78.0.0/16` → `SITE-SPB-DC` сохранено. Другие подсети, Sites, Site Links, DC placement, DNS, GPO, Exchange, PVE, маршрутизация и firewall не менялись.

## Проверка сразу после изменения

- В AD присутствуют только два соответствия: `10.78.0.0/16` → `SITE-SPB-DC` и `10.10.0.0/16` → `SITE-MMK`.
- `DC2` остаётся в `SITE-MMK`, `SPB-DC1-AL` — в `SITE-SPB-DC`; оба GC.
- `repadmin /replsummary`: 0 ошибок по доступным направлениям. Из SPB-DC1 остаётся известное ограничение удалённого опроса DC2 (`110`) из SSH-сессии без делегирования, не ошибка репликации.
- `dcdiag /test:Advertising /test:SysVolCheck /test:DNS /q` не выдал ошибок.
- Exchange: DAG02 operational `SPB-MX3`, `SPB-MX4`; все реплицируемые копии на SPB-MX4 `Healthy`, copy queue 0. Одиночная `Mailbox Database 1610298417` остаётся mounted как известное исходное исключение.

## Обязательная контрольная точка

На DC2, чтобы немедленно получить новый объект Configuration, выполнить:

    repadmin /replicate localhost SPB-DC1-AL "CN=Configuration,DC=aurora-logistics,DC=local" /force
    repadmin /replsummary

Затем на одном рабочем ПК с адресом `10.10.x.x`:

    nltest /dsgetsite
    nltest /dsgetdc:aurora-logistics.local
    gpupdate /force
    klist get krbtgt

Ожидаемый сайт — `SITE-MMK`, предпочтительный DC — `DC2`. Проверить Outlook тестовым исходящим и входящим сообщением; при наличии OWA — открыть его.

## Откат

Если клиентская проверка выявит проблему, удалить только новое соответствие:

    Remove-ADReplicationSubnet -Identity '10.10.0.0/16' -Confirm:$false

Затем реплицировать раздел Configuration на DC2 и повторить проверки. `10.78.0.0/16` и настройки Sites не менять.

## Следующий шаг

Не назначать новые подсети, пока не завершится эта контрольная точка. После неё отдельно определить следующую целевую сеть, а не массово переносить оставшиеся диапазоны.
