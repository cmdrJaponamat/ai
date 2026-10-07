# AD Sites rollout — шаг 3: переходный Site Link

**Время:** 2026-10-07 16:41 MSK
**Статус:** выполнен; дальнейший rollout остановлен на контрольной точке

## Изменение

Создан `SL-AD-TRANSITION`:

- Sites: `Default-First-Site-Name`, `SITE-SPB-DC`, `SITE-MMK`;
- cost: `100`;
- replication frequency: `15` минут;
- пустой атрибут Schedule означает schedule 24×7.

Ни одного AD Subnet не создано; оба DC остаются в
`Default-First-Site-Name`. Поэтому клиентский DC Locator, DNS/GPO и Exchange
маршрутизация не менялись.

## Проверка после изменения

- Link содержит все три требуемых DN Sites.
- `repadmin /replsummary` по-прежнему показывает 0 failures из 5 в обоих
  направлениях; `dcdiag` Advertising/SYSVOL/DNS без ошибок.
- На MX4 все пассивные копии Healthy, copy-очереди 0; активная однокопийная
  `Mailbox Database 1610298417` остаётся Mounted.

## Ограничение контроля

Прямая проверка нового config-объекта на DC2 не завершена:

- SSH на `10.10.20.50:22` закрыт;
- DC2 не размещён на доступных PVE1/PVE2;
- `repadmin /showobjmeta DC2 ...` и принудительный `repadmin /syncall` из
  SSH key-only сеанса на DC1 получили `Access denied` (отсутствует
  делегированный удалённый Kerberos-токен). Это не является replication
  failure и не изменило AD, но не даёт доказать получение config-объекта
  вторым DC из текущего канала доступа.

## Стоп-условие

Не переносить `spb-dc1-al` или `dc2` до read-only подтверждения на DC2, что
`SITE-SPB-DC`, `SITE-MMK` и `SL-AD-TRANSITION` присутствуют. Подходящие
способы: SSH/WinRM на DC2 с ключом, интерактивная доменная сессия на DC2 либо
команда проверки, выполненная уполномоченным администратором на DC2.

## Откат

Пока link не обслуживает DC и не содержит subnet, удалить только его:

```powershell
Remove-ADReplicationSiteLink -Identity 'SL-AD-TRANSITION' -Confirm:$false
```

После этого при необходимости удалить пустые `SITE-MMK` и `SITE-SPB-DC`.
