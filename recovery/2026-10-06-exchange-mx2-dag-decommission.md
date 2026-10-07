# Вывод SPB-MX2 из Exchange DAG02

**Дата:** 2026-10-06
**Выведенный сервер:** `SPB-MX2`, PVE2 VM `111`, IP `10.78.3.61`
**Оставшийся DAG:** `SPB-MX3`, `SPB-MX4`; witness `spb-wts-al.aurora-logistics.local`

## Выполнено

1. Проверены копии БД: у MX3 и MX4 все требуемые копии были `Mounted` либо
   `Healthy`; CopyQueue равнялась нулю.
2. Единственная активная БД на MX2, `Admins`, вручную перенесена на MX4:
   `Succeeded`, `NumberOfLogsLost=0`.
3. На MX4 отменён временный запрет активации:
   `DatabaseCopyAutoActivationPolicy=Unrestricted`.
4. Первоначально в источники Send Connector `aurora-logistics.ru` и `KSMG`
   были добавлены `SPB-MX3` и `SPB-MX4`. Это вызвало отказ KSMG при relay
   через MX4; 2026-10-07 оба коннектора были возвращены к единственному
   источнику `SPB-MX3`.
5. MX2 переведён в maintenance:
   `DatabaseCopyAutoActivationPolicy=Blocked`,
   `DatabaseCopyActivationDisabledAndMoveNow=True`, HubTransport сначала
   `Draining`, после пустой очереди — `Inactive`.
6. Удалены только конфигурационные объекты восьми копий вида `DB\SPB-MX2`.
   Файлы старых EDB/log на отключённой VM не удалялись.
7. Выполнено штатное `Remove-DatabaseAvailabilityGroupServer` для MX2.
8. VM111 остановлена через Proxmox штатным `qm shutdown`; её конфигурация и
   все диски сохранены.

## Проверка после вывода

- `DAG02`: members/operational members — `SPB-MX3`, `SPB-MX4`.
- Оба Cluster Node — `Up`.
- Все оставшиеся копии — `Mounted` или `Healthy`; в момент финальной проверки
  `Krasnoyarsk\SPB-MX4` был `Healthy`, CopyQueue 0.
- `Test-ServiceHealth` на MX3 и MX4: все required services running.
- Transport queues MX3/MX4 пусты.
- Nginx обратного прокси указывает Exchange HTTP-проксирование на MX3
  (`10.78.3.62`), без ссылки на MX2.
- После первоначального отказа relay KSMG был дополнительно настроен
  администратором для MX4 (`10.78.3.63`). Проверка SMTP envelope без `DATA`
  вернула `250 2.1.5 Ok`; поэтому MX3 и MX4 являются источниками обоих
  рабочих исходящих коннекторов.

## Известные ограничения

- После вывода MX2 DAG состоит из двух членов с file-share witness. Он
  работоспособен, но отказ любого оставшегося узла лишит базы резервной копии.
- `spb-mdb3` имеет только копию на MX3, а стандартная
  `Mailbox Database 1610298417` — только на MX4. Поэтому соответствующие
  проверки DatabaseRedundancy/DatabaseAvailability ожидаемо предупреждают.
- Сразу после недавно завершённого seed replay queue пассивной
  `Krasnoyarsk\SPB-MX4` может колебаться при статусе `Healthy`.

## Откат

Не включать VM111 в рабочую схему простым запуском: сервер больше не состоит
в DAG и его Exchange Transport отключён.

Если потребуется вернуть MX2 как участника DAG:

1. Запустить VM111 и проверить AD/DNS/сеть и Exchange services.
2. Вернуть `HubTransport` в `Active` для requester `Maintenance` только после
   явного решения использовать его как транспорт.
3. При необходимости вернуть MX2 в `SourceTransportServers` нужных Send
   Connector.
4. `Add-DatabaseAvailabilityGroupServer -Identity DAG02 -MailboxServer SPB-MX2`.
5. Создать новые копии нужных БД `Add-MailboxDatabaseCopy` и дождаться полного
   seed до `Healthy`.

До отдельного решения об окончательном списании VM111 и её старых дисков не
удалять.

## Будущая балансировка внешней почты

KSMG уже разрешает SMTP relay от `10.78.3.63`; envelope-проверка без передачи
содержимого письма успешно выполнена. Следующая проверка уровня сервиса —
контролируемая доставка на согласованный внешний почтовый ящик. Если потребуется
быстрый откат, достаточно вернуть оба SourceTransportServers к `SPB-MX3`.
