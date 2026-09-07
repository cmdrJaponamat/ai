# Вывод SPB-MX2 из Exchange/DAG maintenance

Дата: 2026-09-07. Статус: завершено.

## Причина

Во время проверки жалобы на задержку входящей почты выяснилось, что
`SPB-MX2` после предыдущего окна с Synology был запущен, но оставался полностью
в Exchange/DAG maintenance. Вся обработка выполнялась `SPB-MX3`; на нём
кратковременно накопилось 23 сообщения с ошибкой
`432 4.3.2 STOREDRV.Deliver; recipient thread limit exceeded`. Очередь
самостоятельно опустела, KSMG и SMTP-путь до MX3 оставались работоспособны.

## Предпроверка

- все девять активных баз были `Mounted` на SPB-MX3;
- на SPB-MX2 четыре пассивные копии были `Healthy`, queue 0/0;
- четыре ранее повреждённые копии `kras`, `MailBoxDB_AL_new`, `mmk` и
  `Krasnoyarsk` оставались `FailedAndSuspended`;
- SPB-MX2 был `Paused`, activation disabled, policy `Blocked`;
- `ServerWideOffline` и транспортные компоненты были `Inactive`;
- Exchange-диски Windows были online/Healthy, обязательные службы запущены.

## Выполнено

Штатно выполнена обратная последовательность maintenance:

1. `ServerWideOffline=Active` с requester `Maintenance`;
2. `Resume-ClusterNode SPB-MX2`;
3. `DatabaseCopyActivationDisabledAndMoveNow=False`;
4. `DatabaseCopyAutoActivationPolicy=Unrestricted`;
5. `HubTransport=Active` с requester `Maintenance`;
6. удалено одноразовое задание
   `Codex-Synology-Maintenance-Shutdown`.

Активные базы на SPB-MX2 принудительно не переносились. Повреждённые копии не
возобновлялись и не reseed'ились.

## Проверка

- cluster node SPB-MX2: `Up`;
- `ServerWideOffline`, `HubTransport`, `FrontendTransport`: `Active`;
- все обязательные роли `Test-ServiceHealth`: running;
- activation policy: `False` / `Unrestricted`;
- здоровые копии SPB-MX2 сохранили `Healthy`, queue 0/0;
- queue SPB-MX2 пуста, очередь доставки SPB-MX3 опустела;
- KSMG принимает внешние сообщения и получает `250 2.6.0` от SPB-MX3;
- shutdown task отсутствует.

`Test-Mailflow` не создал probe: на SPB-MX2 сейчас нет активной mailbox
database с системным monitoring mailbox. Это ограничение теста, а не отказ
SMTP; фактическая доставка подтверждена очередями и журналом KSMG.

## Откат

Если потребуется вернуть SPB-MX2 в maintenance:

1. перевести `HubTransport` в `Draining` requester `Maintenance` и выполнить
   `Redirect-Message` на SPB-MX3;
2. включить `DatabaseCopyActivationDisabledAndMoveNow=True` и policy
   `Blocked`;
3. выполнить `Suspend-ClusterNode SPB-MX2`;
4. установить `ServerWideOffline=Inactive` requester `Maintenance`;
5. проверить, что все активные базы остаются на SPB-MX3 и queues пусты.

Повторно создавать shutdown task без отдельной необходимости не требуется.
Reboot/relogin: не требуется.
