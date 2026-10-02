# Подготовка SPB-MX4 к установке Exchange

Дата: 2026-10-01

## Цель

Подготовить VM `SPB-MX4` (10.78.3.63, VMID 135) к установке роли Mailbox
Exchange Server 2019 для последующего добавления в существующий DAG.

## Подтверждённое исходное состояние

- Windows Server 2019 Standard, домен `aurora-logistics.local`;
- `admin-al` имеет локальные административные права;
- на C: 174.1 GiB свободно; новые data-диски ещё не размечены;
- `.NET Framework` release `461814` (4.6.2), prerequisites Exchange не
  установлены;
- на сервере уже есть pending reboot (`CBS RebootPending`) до начала работ;
- действующий SPB-MX2 использует Exchange Server 2019 CU11, build
  `15.2.986.5`; на MX4 Exchange ещё не установлен.

## Безопасная последовательность

1. Выполнить уже требующуюся перезагрузку MX4 и дождаться SSH/WinRM.
2. Установить только documented Mailbox prerequisites для Windows Server 2019,
   .NET Framework 4.8, VC++ 2012/2013, UCMA 4.0 и IIS URL Rewrite.
3. Перезагрузить, проверить компоненты и отсутствие pending reboot.
4. Не запускать Exchange Setup и не создавать DB/DAG до отдельного решения о
   версии CU: CU11 снят с поддержки, а новый член DAG должен быть совместим с
   текущими участниками.

## Выполнено

- Выполнена исходно ожидавшаяся перезагрузка Windows; после неё служба `sshd`
  оказалась выключена и с manual startup, поэтому переведена в `Automatic` и
  запущена. Проверка после второй перезагрузки: SSH по ключу работает,
  `sshd` — `Running/Automatic`.
- Установлен полный documented набор Windows features для Exchange 2019
  Mailbox на Desktop Experience: IIS, WCF activation/TCP Port Sharing,
  RPC-over-HTTP, Server Media Foundation, кластерные RSAT-компоненты,
  Windows Identity Foundation и RSAT-ADDS. Проверка списка features показала
  `Missing=0`.
- С официального Microsoft URL загружен offline installer .NET Framework 4.8;
  перед запуском проверена действительная подпись Microsoft Corporation.
  Установлен silently и применён перезагрузкой. Текущий release `528049`
  (4.8), pending reboot отсутствует.

## Ещё не выполнено

- Exchange Server Setup запускался один раз, но не прошёл prerequisite check:
  ключевая SSH-сессия не предоставила Exchange пригодный domain network
  credential. Лог фиксирует `The supplied credential for
  'AURORA-LOGISTIC\\admin-al' is invalid`. Роль Mailbox, Exchange
  organization/DAG/DB/коннекторы не изменялись.
- До установки Exchange нужно получить и проверить согласованный дистрибутив
  CU. У текущих MX-серверов CU11 (`15.2.986.5`), который устарел и не должен
  быть новым постоянным базисом без плана обновления всех участников.
- Из выбранного дистрибутива необходимо поставить его `UCMARunTimeSetup.exe`
  (UCMA 4.0). VC++ 2012 x64, VC++ 2013 x64 и IIS URL Rewrite также должны
  быть установлены в согласованных с выбранным CU версиях, затем следует
  выполнить финальный readiness check.

## Диски Exchange: состояние на 2026-10-02 09:05 MSK

- VM135 получила четыре пустых data-диска: 7.8 TiB, 1.7 TiB, 600 GiB и
  20 GiB. До начала работ все были RAW/offline/read-only вследствие SAN
  policy Windows; данные или разделы на них отсутствовали.
- Подготовка предусмотрена как отдельные ReFS/64 KiB volumes:
  `E:` `EXCH-DB01`, `F:` `EXCH-DB02`, `G:` `EXCH-LOGS`, `H:`
  `EXCH-MAINT`; integrity streams для данных будут отключены после создания.
  Разделение БД и журналов соответствует Microsoft Exchange Preferred
  Architecture.
- На момент записи DiskPart PID 6416 последовательно форматирует пустой
  первый том. Не прерывать и не запускать второй форматирующий процесс.
  Диски 2–4 остались RAW/offline, то есть ещё не изменялись.

## Коррекция SAN-policy: 2026-10-02 09:20 MSK

- Диагностика `diskpart san` подтвердила `Offline Shared` (`SanPolicy=2`).
  Это объясняет, почему Windows после загрузки автоматически переводила
  virtual SCSI-диски VM135 offline/read-only.
- После двух подтверждённых владельцем forced reset VM135 для снятия
  прерванных DiskPart процессов применено `san policy=OnlineAll`. Для этой
  VM это корректно: её четыре виртуальных data-диска не являются одним
  одновременно подключаемым Windows shared LUN. Если в будущем появится
  действительно общий writable-диск, политику нужно вернуть `OfflineShared`.
- Завершён `H:`: label `EXCH-MAINT`, NTFS, allocation unit 64 KiB, Healthy.
- ReFS formatting of G was stopped because it did not progress. A subsequent
  NTFS attempt was also interrupted before a filesystem was created. After the
  later confirmed reset there is no active DiskPart process: Disk1 and Disk3
  contain only empty GPT partitions without a filesystem, Disk2 is RAW/offline,
  and H remains healthy NTFS/64 KiB.

## Проверка PVE/NAS пути: 2026-10-02 10:04 MSK

- PVE1 → `10.78.5.10` passed ICMP 5/5 with 0% loss and 0.067 ms average.
- The new Synology target is `LOGGED_IN`; `/dev/sde` is present at 26 TiB and
  PVE kernel logs contain no error for this device.
- A direct 32 MiB read from `/dev/sde`, plus a direct write/read to a fresh
  64 MiB temporary LV in `vg_synology_exch3`, succeeded. The LV was removed.
- This demonstrates that the current NAS/L2/iSCSI/PVE block path is working at
  a basic level. It is not a certification of sustained performance; resume
  guest formatting only one operation at a time.

## Имена томов MX3/MX4

MX3 uses the following existing convention: `E:` `DB`, `F:`
`DB-Murmansk`, `G:` `DB-Krasnoyarsk`, `H:` `SystemMailboxesDB`.
MX4 `H:` has been renamed to `SystemMailboxesDB` and remains NTFS/64 KiB,
Healthy. When the remaining empty MX4 disks are formatted through RDP, use the
same E/F/G labels respectively.

## Блокер установки

`admin-al` имеет `Organization Management`, а secure channel с доменом
исправен. Но тестовая задача с полным credential отклонила пароль из
локального MikroTik/ansible vault; этот пароль не является действующим
доменным паролем либо не подходит для данного UPN. Для запуска Setup нужен
действующий пароль `admin-al@aurora-logistics.local` или интерактивная
доменная RDP/console-сессия под этой учётной записью. Тестовая задача не была
создана и ничего не сохранила.

## Откат

Установка Windows roles и .NET обратима только через удаление компонентов и
перезагрузку; до Exchange Setup нет изменений организации Exchange, DAG,
баз данных или маршрутизации.
