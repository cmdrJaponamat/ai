# Отключение пользовательских ящиков DB-FIRED-01

Дата: 2026-10-27 (MSK)  
Объект: `DB-FIRED-01`, SPB-MX4/MX3.

## Причина и допуск

Владелец подтвердил вывод базы в холодное хранение и явно поручил отключить
все пользовательские ящики в ней. Успешная отдельная Veeam-точка
`bkp_exchange_fired01_cold` создана 26.10.2026, а восстановление ящика в
PST проверено владельцем. Последний ежедневный DAG backup также завершился
Success 27.10.2026 в 09:37.

## Исходное состояние

- `DB-FIRED-01` Mounted на MX4, пассивная копия MX3 Healthy, обе очереди 0.
- В базе 61 connected mailbox, и все имеют `RecipientTypeDetails=UserMailbox`.
- Нет активных/незавершённых MoveRequest, disconnected mailbox, arbitration,
  audit или public-folder mailbox.
- Два monitoring HealthMailbox привязаны к DB-FIRED-01; они не входят в
  отключение. Exchange должен убрать их при `Remove-MailboxDatabase`.

## Выполняемое изменение

Для каждого объекта из `Get-Mailbox -Database DB-FIRED-01` выполняется
`Disable-Mailbox -Confirm:$false`. Команда отключает почтовый ящик от AD,
но не удаляет AD-учётную запись. Не используются `Remove-Mailbox` и операции
с HealthMailbox.

## Откат и ограничения

До удаления самой EDB ящик остаётся disconnected в базе на период
`MailboxRetention=30 дней` и может быть подключён обратно штатным
`Connect-Mailbox`. После удаления DB-FIRED-01 источником восстановления
будет проверенная холодная Veeam-точка.

## Результат и проверка

- Успешно выполнен `Disable-Mailbox` для всех 61 заранее проверенных
  `UserMailbox`, включая `adminspb`; ошибок не получено.
- Повторный `Get-Mailbox -Database DB-FIRED-01` вернул 0 connected mailbox.
- `Get-MailboxStatistics -Database DB-FIRED-01` показывает ровно 61 запись
  с `DisconnectReason=Disabled`.
- EDB, DAG-копия, monitoring HealthMailbox и физические диски намеренно
  оставлены без изменений до отдельного подтверждённого этапа удаления.
