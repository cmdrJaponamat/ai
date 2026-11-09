# Ограничение размера вложений Exchange

Дата: 2026-11-09. Узлы: SPB-MX3 и SPB-MX4, Exchange 15.2.

## Цель

Владелец выбрал максимум 20 МБ на одно вложение. Для передачи файла такого размера после MIME-кодирования предел всего письма выбран 28 МБ. Правило транспорта должно отклонять вложения от 20 МБ; общий предел письма не позволит обойти его несколькими меньшими файлами.

## Состояние до изменения

- Организация: `MaxSendSize=70MB`, `MaxReceiveSize=70MB`.
- Единственный включённый исходящий Send Connector `KSMG`: `MaxMessageSize=100MB`.
- Пять включённых Receive Connector на MX3: каждый `70MB`; пять на MX4: каждый `36MB`.
- 319 обычных ящиков: `MaxSendSize=Unlimited`, `MaxReceiveSize=Unlimited`; у служебного DiscoverySearchMailbox оба `100MB`.
- Правил с `AttachmentSizeOver`/`MessageSizeOver` не было. Четыре отключённых Send Connector остаются вне изменения.
- `WhatIf` для организации, KSMG и нового правила прошёл.

## Изменение

В 18:29 MSK установлены организационные send/receive, включённый KSMG Send Connector и все 10 включённых Receive Connector в `28MB`; создано правило `AL - Reject attachments 20 MB or larger` с `AttachmentSizeOver=20MB`, `Mode=Enforce`, `State=Enabled`, приоритетом 16 и отклонением с пояснением на английском и русском языках. Правило применяется ко всем письмам; в существующих правилах `StopRuleProcessing=False`.

Конфигурация KSMG как отдельного шлюза не менялась; Exchange ограничивает доставку из него и отправку в него. Отключённые Send Connector и лимиты отдельных ящиков не менялись. Предел `28MB` относится ко всему MIME-письму; вложение ровно около 20 МБ может не пройти при большом теле или дополнительном кодировании.

## Проверка

- MX3 и MX4 независимо показывают `28MB` для организации, KSMG Send Connector и каждого из пяти локальных активных Receive Connector; правило включено и указывает `20MB`.
- SMTP EHLO на порту 25 обоих серверов объявляет `SIZE 29360128` (28 MiB).
- Службы `MSExchangeTransport` и `MSExchangeFrontEndTransport` на обоих узлах работают, все проверенные очереди пусты. Тестовое крупное письмо не отправлялось.

## Откат

```powershell
Set-TransportConfig -MaxSendSize 70MB -MaxReceiveSize 70MB
Set-SendConnector -Identity 'KSMG' -MaxMessageSize 100MB
Get-ReceiveConnector -Server SPB-MX3 | Where-Object Enabled | Set-ReceiveConnector -MaxMessageSize 70MB
Get-ReceiveConnector -Server SPB-MX4 | Where-Object Enabled | Set-ReceiveConnector -MaxMessageSize 36MB
Disable-TransportRule -Identity 'AL - Reject attachments 20 MB or larger'
```

После проверки можно удалить новое правило отдельно. Перезапуск служб, повторный вход и перезагрузка не требуются; перенос почтовых потоков не планируется.
