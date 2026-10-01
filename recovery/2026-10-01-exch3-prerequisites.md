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

- Exchange Server Setup не запускался, роль Mailbox не установлена, Exchange
  organization/DAG/DB/коннекторы не изменялись.
- До установки Exchange нужно получить и проверить согласованный дистрибутив
  CU. У текущих MX-серверов CU11 (`15.2.986.5`), который устарел и не должен
  быть новым постоянным базисом без плана обновления всех участников.
- Из выбранного дистрибутива необходимо поставить его `UCMARunTimeSetup.exe`
  (UCMA 4.0). VC++ 2012 x64, VC++ 2013 x64 и IIS URL Rewrite также должны
  быть установлены в согласованных с выбранным CU версиях, затем следует
  выполнить финальный readiness check.

## Откат

Установка Windows roles и .NET обратима только через удаление компонентов и
перезагрузку; до Exchange Setup нет изменений организации Exchange, DAG,
баз данных или маршрутизации.
