# MMK-DC1-AL: подготовка и замена DC2 на Тарана

Актуальный контекст: [recovery-запись](../recovery/2026-11-05-mmk-dc-replacement-preparation.md). Команды ниже предназначены для **интерактивной консоли администратора**. Новый сервер пока недоступен удалённо; действия на нём не выполнены.

## Зафиксированная схема

| Объект | Значение |
| --- | --- |
| Домен | `aurora-logistics.local` |
| Существующий AD Site | `SITE-MMK` |
| Старый DC | `DC2`, `10.10.20.50`, writable GC, Windows Server 2019 |
| Новый DC | `MMK-DC1-AL`, сейчас `192.168.203.40` в СПб |
| Адрес для одновременной работы | `10.10.20.51/24`, шлюз `10.10.20.1` |
| Адрес после вывода DC2 | `10.10.20.50/24` |
| DNS в СПб для подготовки | `SPB-DC1-AL`, `10.78.3.50` |
| DNS на Тарана до демоции DC2 | `DC2` `10.10.20.50`, затем `SPB-DC1-AL` `10.78.3.50` |

`10.10.20.51` исключён из DHCP-пула `AL-MMK`; до присвоения повторно проверить отсутствие статического узла с этим адресом. `192.168.203.0/24` принадлежит `SITE-SPB-MILLION`, а `10.10.0.0/16` — `SITE-MMK`. Пять FSMO-ролей находятся на `SPB-DC1-AL`. Новый AD Site создавать не нужно.

## 1. Пока сервер в СПб — подготовить и при готовности повысить до DC

На локальной консоли открыть 64-разрядный Windows PowerShell **от администратора**. Проверить систему, сеть, диски и время:

```powershell
hostname
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,LastBootUpTime
Get-NetIPConfiguration
Get-Volume | Select-Object DriveLetter,FileSystem,SizeRemaining,Size
w32tm /query /source
Resolve-DnsName -Server 10.78.3.50 -Type SRV _ldap._tcp.dc._msdcs.aurora-logistics.local
Test-NetConnection 10.78.3.50 -Port 389
```

Проверить активацию Windows, обновления безопасности, агент удалённого доступа, резервное копирование, доступ к консоли после перевозки и состояние дисков. Проверить, что текущий адрес действительно `192.168.203.40`, а внутренняя DNS-запись домена разрешается через `10.78.3.50`. Если текущий DNS на сетевой карте не является доменным, на время подготовки установить `10.78.3.50` как DNS этой карты. Публичный DNS на доменном сервере не задавать.

Если имя ещё не задано, выполнить и дождаться перезагрузки:

```powershell
Rename-Computer -NewName 'MMK-DC1-AL' -Restart
```

После перезагрузки вступить в домен под учётной записью, имеющей право добавлять серверы, и снова дождаться перезагрузки:

```powershell
Add-Computer -DomainName 'aurora-logistics.local' -Credential (Get-Credential) -Restart
```

Проверить результат и установить только бинарные компоненты AD DS:

```powershell
hostname
(Get-CimInstance Win32_ComputerSystem).Domain
nltest /dsgetsite
nltest /dsgetdc:aurora-logistics.local /force
Test-ComputerSecureChannel
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools
Get-WindowsFeature AD-Domain-Services,DNS,Print-Server
```

На текущем адресе ожидается `SITE-SPB-MILLION`. `10.10.20.51` пока не задавать. Повышение до DC можно выполнить уже здесь, если проверены доступ к `SPB-DC1-AL` по требуемым портам AD, DNS, время, резервное копирование и здоровье существующих DC. В мастере повышения выбрать **«Добавить контроллер домена в существующий домен»**, DNS, GC и **текущий** сайт `SITE-SPB-MILLION`; источником репликации выбрать `SPB-DC1-AL`. В PowerShell эквивалент:

```powershell
$domainCredential = Get-Credential
$dsrmPassword = Read-Host 'Новый пароль DSRM' -AsSecureString
Install-ADDSDomainController `
  -DomainName 'aurora-logistics.local' `
  -SiteName 'SITE-SPB-MILLION' `
  -ReplicationSourceDC 'SPB-DC1-AL.aurora-logistics.local' `
  -InstallDns `
  -Credential $domainCredential `
  -SafeModeAdministratorPassword $dsrmPassword
```

До повышения проверить здоровье текущих DC по разделу 2. После перезагрузки проверить `Get-SmbShare SYSVOL,NETLOGON`, `repadmin /showrepl MMK-DC1-AL`, `repadmin /replsummary`, `dcdiag /s:MMK-DC1-AL /test:Advertising /test:SysVolCheck /test:DNS /q` и DNS SRV для `SITE-SPB-MILLION`. Убедиться, что новый DC реально обслуживает запросы в этом сайте: клиенты сайта могут начать выбирать его сразу после публикации SRV. До перевозки сохранить резервную копию System State и выполнять штатное выключение. Во время перевозки недоступность этого DC не должна приводить к отказу входа и политик на площадке СПб; проверить выбор другого DC до отключения.

Пароль DSRM сохранить в утверждённом хранилище. Не использовать `-SkipPreChecks`. Проверенные драйверы и пакеты принтеров можно подготовить заранее; очереди публиковать после проверки печати на целевой площадке. Назначать адрес Мурманска только с локальной консоли после перевозки.

## 2. До повышения — контроль старого DC2

На `DC2` или из доверенной административной сессии снять состояние и резервную копию **System State** действующим средством резервного копирования. Сверить дополнительные роли и привязанные сервисы (DNS, DHCP, печать, задачи, сертификаты, явные ссылки на имя `DC2`). Известно, что FSMO на `DC2` нет, но это не заменяет проверку остальных ролей. До смены DC сохранить результаты:

```powershell
repadmin /replsummary
repadmin /showrepl DC2
dcdiag /s:DC2 /test:Advertising /test:SysVolCheck /test:DNS /q
Get-WindowsFeature | Where-Object Installed | Select-Object Name,DisplayName
```

На `AL-MMK` повторно проверить отсутствие активной DHCP-аренды и ARP MAC для `.51`; на Windows проверить отсутствие ответа и конфликтов адресов. Проверить межсетевой доступ к новому `.51` от `DC2`, `SPB-DC1-AL` и клиентов: DNS, Kerberos, LDAP, SMB, RPC и динамические порты репликации. Один лишь `ping` недостаточен.

## 3. На Тарана — ввести подготовленный DC на временном адресе

На локальной консоли нового сервера установить **статически** `10.10.20.51/24`, шлюз `10.10.20.1`, DNS сначала `10.10.20.50`, затем `10.78.3.50`. Удалить старый `192.168.203.40` с сетевого интерфейса. Проверить:

```powershell
ipconfig /all
nltest /dsgetsite
Test-NetConnection 10.10.20.50 -Port 389
Test-NetConnection 10.78.3.50 -Port 389
Resolve-DnsName -Server 10.10.20.50 -Type SRV _ldap._tcp.dc._msdcs.aurora-logistics.local
w32tm /query /source
```

Для уже повышенного в СПб DC **переместить объект сервера** в `SITE-MMK` (консоль «Сайты и службы Active Directory» или команда ниже), затем перерегистрировать записи и проверить репликацию. Одной смены IP для переноса объекта DC между сайтами недостаточно.

```powershell
Move-ADDirectoryServer -Identity 'MMK-DC1-AL' -Site 'SITE-MMK'
ipconfig /registerdns
nltest /dsregdns
repadmin /kcc MMK-DC1-AL
```

После репликации конфигурации проверить, что `Get-ADDomainController -Identity MMK-DC1-AL` показывает `SITE-MMK` и `.51`, а DNS-имя не возвращает прежний `192.168.203.40`. Проверить SRV нового сайта и убрать устаревшие записи старого сайта, если они остались. Если DC ещё не повышали, ожидать `SITE-MMK` по `nltest /dsgetsite`; при исправной репликации старого DC2 и связи с ЦОД выполнить повышение в администраторском PowerShell:

```powershell
$domainCredential = Get-Credential
$dsrmPassword = Read-Host 'Новый пароль DSRM' -AsSecureString
Install-ADDSDomainController `
  -DomainName 'aurora-logistics.local' `
  -SiteName 'SITE-MMK' `
  -ReplicationSourceDC 'DC2.aurora-logistics.local' `
  -InstallDns `
  -Credential $domainCredential `
  -SafeModeAdministratorPassword $dsrmPassword
```

Пароль DSRM сохранить в утверждённом хранилище. Не использовать `-SkipPreChecks` и не отключать автоматический reboot после успешного повышения. После ввода DC в `SITE-MMK` на `.51` проверить на новом сервере:

```powershell
Get-ADDomainController -Identity MMK-DC1-AL | Select-Object HostName,IPv4Address,Site,IsGlobalCatalog,IsReadOnly
Get-SmbShare SYSVOL,NETLOGON
repadmin /replsummary
repadmin /showrepl MMK-DC1-AL
dcdiag /s:MMK-DC1-AL /test:Advertising /test:SysVolCheck /test:DNS /q
Resolve-DnsName -Server 10.10.20.51 -Type SRV _ldap._tcp.SITE-MMK._sites.dc._msdcs.aurora-logistics.local
```

Подтвердить приём изменений с обеих сторон за полный цикл репликации. На одном доменном ПК Мурманска временно проверить DNS нового DC, `Test-ComputerSecureChannel -Server MMK-DC1-AL`, `\\MMK-DC1-AL\SYSVOL`, вход и `gpupdate /force`. Сверить события AD DS, DNS и DFS Replication. Старый `DC2` пока оставлять включённым.

## 4. Штатно вывести DC2 и вернуть адрес `.50`

Только после успешных проверок нового DC и резервных копий на старом DC2 выполнить штатную демоцию через Server Manager либо `Uninstall-ADDSDomainController` с интерактивным вводом учётных данных и пароля локального администратора. **Не** применять принудительную демоцию при исправном DC. Проверить, что объект NTDS и DNS SRV старого DC исчезли после репликации; сохранить журнал демоции.

После демоции и reboot выключить `DC2` или снять с него `10.10.20.50`, убедиться, что адрес действительно свободен. Только затем с локальной консоли изменить IP нового `MMK-DC1-AL` с `.51` на `10.10.20.50`, оставив `/24` и шлюз `.1`. Для DNS-клиента нового DC установить `10.78.3.50` и его локальный DNS (`127.0.0.1` либо `10.10.20.50`), проверив доступность обеих зон. На статическом DC обновить DNS-регистрацию и проверить записи на обоих DNS:

```powershell
ipconfig /registerdns
nltest /dsregdns
repadmin /replsummary
dcdiag /s:MMK-DC1-AL /test:Advertising /test:SysVolCheck /test:DNS /q
Resolve-DnsName -Server 10.78.3.50 MMK-DC1-AL.aurora-logistics.local
Resolve-DnsName -Server 10.10.20.50 MMK-DC1-AL.aurora-logistics.local
```

Проверить на клиенте VLAN 30, который получает DNS `10.10.20.50` из DHCP: разрешение имени домена, выбор `SITE-MMK`, вход, Kerberos, SYSVOL и применение GPO. Проверить другие мурманские сети, а также приложения с явными ссылками на имя `DC2`: повторное использование IP не исправляет ссылки на старый hostname. Если старый DNS-клиент или маршрутизатор где-либо указывает `DC2` по имени, обновить отдельно.

## 5. Печать на том же DC

После устойчивой работы AD/DNS установить роль `Print-Server`, проверить, что корпоративная GPO не отключает `Spooler`, и включить только подтверждённые очереди для площадки. Управлять драйверами только от доверенного администратора: выбирать подписанные пакеты, по возможности пакетные драйверы, использовать статические TCP/IP-порты вместо WSD. Не ослаблять требование повышения прав для установки драйверов через Point and Print. В каталоге Тарана обнаружены устройства на `10.10.30.36`, `.39` и `.45`; их физическое наличие, модели и адреса проверить перед созданием очередей, особенно `.45` с устаревшей арендой.

Совмещение Print Spooler и DC противоречит рекомендации Microsoft для безопасности контроллеров. Ограничить доступ к очередям и управление ими, не выдавать принтерным администраторам права администрирования DC, своевременно обновлять ОС и драйверы, контролировать журнал PrintService. Отдельно проверить сетевые правила для клиентских VLAN и принтеров; простое ограничение SMB/RPC по IP не обеспечивает полной изоляции печати от AD на одной ОС. После настройки сохранить экспорт конфигурации печати через Print Management/PrintBRM и выполнить пилотную печать от обычного пользователя.

## Критерий завершения

`SITE-MMK` содержит новый writable GC/DNS `MMK-DC1-AL` на `10.10.20.50`, `DC2` штатно демотирован, репликация и DFSR без ошибок, несколько клиентских сетей проходят вход и GPO через новый DC, DHCP VLAN 30 продолжает выдавать действующий DNS `.50`, тестовые очереди печатают. До выполнения всех пунктов старый сервер или его резервная копия сохраняются для восстановления.
