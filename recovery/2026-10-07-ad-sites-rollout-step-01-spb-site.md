# AD Sites rollout — шаг 1: пустой SITE-SPB-DC

**Время:** 2026-10-07 16:37 MSK
**Статус:** выполнен, контролируемый

## Изменение

На `spb-dc1-al` создан только объект AD Site `SITE-SPB-DC`.

Не создавались AD Subnet, Site Link, connection object; ни один DC не
перемещался между Sites. Изменение не меняет Site, DC Locator, DNS, GPO или
Exchange-путь ни для одного клиента.

## Проверка после изменения

- В AD присутствуют `Default-First-Site-Name` и `SITE-SPB-DC`.
- AD Subnet-объекты по-прежнему отсутствуют.
- `spb-dc1-al` и `dc2` остаются в `Default-First-Site-Name`.
- `repadmin /replsummary`: 0 failures из 5 в обоих направлениях; известная
  diagnostic-особенность чтения сведений с DC2 (`110`) сохраняется и не стала
  новым replication failure.
- На MX4 все пассивные копии баз Healthy; активная однокопийная
  `Mailbox Database 1610298417` остаётся Mounted; очереди copy равны нулю.

Проверить объект сайта непосредственно на DC2 текущим SSH-key-only сеансом
невозможно: `repadmin /showobjmeta DC2 ...` возвращает `DsBindWithCred` access
denied, а SSH на DC2 не слушает. Это ограничение доступа наблюдалось уже до
шага и не является причиной для изменения конфигурации.

## Откат

До создания subnet и переноса DC удаление возможно одной командой на DC1:

```powershell
Remove-ADReplicationSite -Identity 'SITE-SPB-DC' -Confirm:$false
```

Перед откатом ещё раз подтвердить отсутствие Site Link, subnet и объектов DC
в `SITE-SPB-DC`.

## Следующий шаг

Создать пустой `SITE-MMK`; до успешной проверки не создавать Site Link и не
перемещать DC.
