# Exchange Search: восстановление Host Controller на SPB-MX4

Дата: 2026-10-15  
Статус: восстановлено; MoveRequest оставлены приостановленными.

## Симптом

Две заявки на перенос в `DB-FIRED-01` дошли до 20%, затем показывали
`TransientFailureTarget` и нулевую скорость. Отчёты MRS указывали на
`BigFunnelTransientException` при фазе `LoadingMessages` на SPB-MX4.

В Application log SPB-MX4 источник `MSExchangeFastSearch`, Event ID 1010,
содержал отказ подключения к
`net.tcp://localhost:3803/Management/ContentTransformation/FlowService`:
`TCP 10061` (connection refused).

## Причина

На SPB-MX4 (`VM 135`) служба `HostControllerService` была `Stopped` с
типом запуска `Disabled`. Поэтому TCP/3803 не слушался. На SPB-MX3 та же
служба штатно `Running`, `Automatic`, TCP/3803 listening.

## Выполненное изменение

После подтверждения владельца на SPB-MX4 выполнено только:

```powershell
Set-Service -Name HostControllerService -StartupType Automatic
Start-Service -Name HostControllerService
```

## Проверка

- `HostControllerService`: `Running`, `Automatic`;
- `MSExchangeFastSearch`: `Running`, `Automatic`;
- TCP/3803: `Listen` на `0.0.0.0` и `[::]`;
- после запуска новых `MSExchangeFastSearch` ошибок не зарегистрировано;
- обе заявки переноса сохранены владельцем `Suspended`, 20%.

## Откат

Технически прежнее неисправное состояние возвращают:

```powershell
Stop-Service HostControllerService
Set-Service HostControllerService -StartupType Disabled
```

Не выполнять без специальной причины: это снова сделает BigFunnel/MRS
недоступным на MX4.

## Следующий безопасный шаг

Возобновить ровно одну существующую заявку и через 2–5 минут проверить
`StatusDetail`, `BytesTransferredPerMinute` и новые события FastSearch.
