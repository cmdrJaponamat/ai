# Проверка машинного VPN и доменных политик до входа пользователя

**Дата:** 2026-11-03. **Пилот:** `AL-TEST`, затем `AL-SAIKINA`. Изменения в
этой памятке не выполняются автоматически.

## 1. Подготовить проверяемое изменение

- На пилотной OU включить компьютерные политики `Always wait for the network at
  computer startup and logon` и `Startup policy processing wait time`.
  Начать с 60 секунд, затем выбрать время по журналу фактического подключения.
  В доступных отчётах семи включённых GPO для `OU=TEST` эти настройки пока не
  найдены; локальную политику самого клиента ещё не проверяли.
- Изменить безвредный параметр **Computer Configuration** в пилотной GPO и
  записать новое ожидаемое значение. Это позволит отличить применение новой
  политики от ранее сохранённой локальной копии. Для проверки именно
  foreground-расширений (например, startup script или установка MSI) нужна
  отдельная канарейка этого типа и холодная загрузка.
- Убедиться, что физическая сеть доступна до входа в Windows: Ethernet или
  Wi-Fi-профиль уровня компьютера. Пользовательский Wi-Fi, который поднимается
  только после входа, не обеспечит соединение VPN до логина.

## 2. Холодная загрузка без входа пользователя

1. Зафиксировать время, перезагрузить ПК и оставить его на экране входа.
2. На `spb-vpn-srv` убедиться, что `AL-TEST.aurora-logistics.local` появился в
   `/var/log/openvpn-status/openvpn-device-status.log` с адресом
   `10.253.91.x` **до** входа пользователя. В журнале OpenVPN проверить время
   `PUSH_REPLY` и отсутствие TLS/CRL-ошибок.
3. Через RMM, запущенный от `SYSTEM`, проверить на ПК:

```powershell
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$boot
Get-Service OpenVPNService | Select-Object Name, Status, StartType
Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object IPAddress -like '10.253.91.*' |
    Select-Object IPAddress, InterfaceAlias
Get-NetRoute -AddressFamily IPv4 |
    Where-Object { $_.DestinationPrefix -in @('10.78.3.50/32', '10.78.4.253/32') } |
    Select-Object DestinationPrefix, NextHop, InterfaceAlias
nltest /dsgetsite
nltest /dsgetdc:aurora-logistics.local /force
Resolve-DnsName spb-dc1-al.aurora-logistics.local -Server 10.78.4.253
Test-NetConnection 10.78.3.50 -Port 445
Test-Path '\\spb-dc1-al.aurora-logistics.local\SYSVOL'
gpresult /scope computer /r
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-GroupPolicy/Operational'; StartTime = $boot
} -ErrorAction SilentlyContinue |
    Select-Object -First 30 TimeCreated, Id, LevelDisplayName, Message
```

Сравнить время подключения OpenVPN, обнаружения DC и обработки **нового**
значения пилотной GPO. `gpupdate /force` после входа пользователя не доказывает
обработку политики при загрузке. Если туннель поднимается после стартовой
обработки, нужен отдельный повторный запуск компьютерной политики после
проверки DC/SYSVOL; расширения, которым нужен синхронный старт, проверить на
следующей загрузке.

## 3. Проверить AD и сертификат

- На DC1 `nltest /dsaddresstosite:10.253.91.X` должен вернуть `SITE-SPB-DC` и
  точную сеть `10.253.91.0/24`. `Get-ADReplicationSubnet` должен показывать
  этот Site. На DC2 соответствие уже подтверждено командой
  `nltest /server:DC2 /dsaddresstosite:10.253.91.3`.
- На ПК проверить сертификат в `Cert:\LocalMachine\My`: CN компьютера,
  издатель `AL-ISSUING-CA`, EKU Client Authentication, срок действия и наличие
  закрытого ключа. Подключение OpenVPN подтверждает, что служба сейчас может
  воспользоваться ключом.
- Текущий туннель не даёт доступ к CA01 `10.78.20.227`. До массовой волны
  определить и проверить отдельный путь для продления сертификата и CRL/AIA.
  На сервере файл CRL сейчас имеет `nextUpdate=2026-11-05 01:47:23 UTC`;
  автоматическое обновление и повторное подключение после смены CRL должны
  пройти отдельный тест. После перевыпуска машинного сертификата повторно
  запустить `deploy-openvpn-device-client.ps1`, проверить ACL нового закрытого
  ключа и переподключение OpenVPN с новым сертификатом.
- Проверить отказ при отзыве **тестового** сертификата и при попытке с
  неподходящим сертификатом. Сервер сейчас требует цепочку доверенного УЦ,
  Client Authentication EKU и действующий CRL, но не ограничивает сертификат
  конкретным шаблоном компьютера или CN; результат теста с пользовательским
  сертификатом нельзя считать заранее гарантированным.

## 4. Критерий для массовой волны

Туннель поднят без пользователя; клиент получил адрес `10.253.91.x` и
`SITE-SPB-DC`; доступны DC, DNS и SYSVOL; новое значение компьютерной GPO
применилось без ручного `gpupdate`; в журнале GroupPolicy нет ошибки по этой
загрузке; повторная загрузка и продление/отзыв сертификата проверены. Затем
повторить на нескольких ПК из разных домашних сетей и проверить загрузку без
Интернета: ожидание сети должно заканчиваться, не блокируя ПК бесконечно.
