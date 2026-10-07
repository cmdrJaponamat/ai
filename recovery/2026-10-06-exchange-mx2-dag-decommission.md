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

## Актуализация на 2026-10-07

MX2 окончательно исключён из почтовой роли:

- `Get-ExchangeServer` возвращает только `SPB-MX3` и `SPB-MX4`.
- На VM111 отсутствуют служба `MSExchangeIS` и файл
  `C:\Program Files\Microsoft\Exchange Server\V15\Bin\Setup.exe`, то есть
  Exchange штатно деинсталлирован.
- VM111 сейчас существует как технический остаток со старыми дисками и может
  быть включена в Proxmox, но **не является почтовым сервером**, членом DAG,
  SMTP-источником или точкой доступа пользователей.

Рабочая схема теперь состоит только из MX3 и MX4; её точное состояние вынесено
в `recovery/2026-10-07-exchange-current-topology.md`.

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

Не включать VM111 в рабочую схему простым запуском: Exchange на ней уже
деинсталлирован, и запуск VM не создаёт почтовый сервер.

Если потребуется вернуть MX2 как участника DAG:

1. Отдельно решить, действительно ли нужен третий член DAG, а не восстановление
   из резервных копий.
2. Установить Exchange той же версии/CU на подготовленную VM (для сохранённого
   имени — штатным `Setup /Mode:RecoverServer`), затем проверить AD/DNS/сеть.
3. Только после этого добавить сервер в DAG командой
   `Add-DatabaseAvailabilityGroupServer` и создать новые копии БД с полным
   seed до `Healthy`.
4. Не добавлять MX2 в `SourceTransportServers` без отдельной настройки KSMG и
   проверки исходящей доставки.

До отдельного решения об окончательном списании VM111 и её старых дисков не
удалять.

## Будущая балансировка внешней почты

KSMG уже разрешает SMTP relay от `10.78.3.63`; envelope-проверка без передачи
содержимого письма успешно выполнена. Затем выполнен согласованный тест на
`japonamt@ya.ru`: MX4 Message Tracking записал `SENDEXTERNAL` через `KSMG`
с ответом `250 2.1.5 Ok`. Это подтверждает передачу KSMG, но не конечную
доставку: её необходимо подтверждать журналом обработки KSMG. Если потребуется
быстрый откат, достаточно вернуть оба SourceTransportServers к `SPB-MX3`.
