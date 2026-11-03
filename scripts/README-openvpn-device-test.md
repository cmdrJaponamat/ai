# Проверка машинного VPN и доменных политик до входа пользователя

**Дата:** 2026-11-03. **Пилот:** `AL-TEST`, затем `AL-SAIKINA`. Изменения в
этой памятке не выполняются автоматически.

## 1. Подготовить проверяемое изменение

1. На DC1 открыть `gpmc.msc`. В домене `aurora-logistics.local` создать GPO
   `TEST-DeviceVPN-PreLogon` и связать с `OU=TEST`. В OU находятся **пять** ПК;
   поэтому в **Scope → Security Filtering** оставить применение только для
   компьютерного объекта `AL-TEST` (в диалоге выбора включить тип объектов
   **Computers**). В **Delegation → Advanced** проверить у `AL-TEST$` права
   `Read` и `Apply group policy`. Не привязывать тестовую GPO ко всему домену.
2. В редакторе этой GPO включить:
   - **Computer Configuration → Policies → Administrative Templates → System →
     Logon → Always wait for the network at computer startup and logon**;
   - **Computer Configuration → Policies → Administrative Templates → System →
     Group Policy → Specify startup policy processing wait time** = 60 секунд.
     По журналу подключения подобрать большее время при необходимости.
   В отчётах семи ранее связанных GPO эти настройки не найдены; локальную
   политику самого клиента ещё не проверяли.
3. В **Computer Configuration → Policies → Windows Settings → Scripts
   (Startup/Shutdown) → Startup** добавить готовый
   [`vpn-gpo-canary.cmd`](vpn-gpo-canary.cmd). Кнопка **Show Files** открывает
   папку этой GPO в SYSVOL; сначала скопировать файл туда, затем нажать
   **Add** и выбрать его по имени. Файл сохранён в ASCII с переносами CRLF; закрытых
   ключей и паролей в нём нет. Его единственное изменение — локальный файл
   отчёта:

```bat
@echo off
setlocal
set "OUT=C:\ProgramData\Aurora\VpnPilot"
if not exist "%OUT%" mkdir "%OUT%"
(
  echo START=%DATE% %TIME%
  echo COMPUTER=%COMPUTERNAME%
  whoami
  ipconfig ^| findstr /C:"10.253.91."
  nltest /dsgetsite
  nltest /dsgetdc:aurora-logistics.local /force
  powershell.exe -NoProfile -Command "Test-Path '\\spb-dc1-al.aurora-logistics.local\SYSVOL'"
  echo END=%DATE% %TIME%
) > "%OUT%\startup.txt" 2>&1
```

4. На включённом AL-TEST с уже работающим VPN один раз выполнить через RMM
   `gpupdate /target:computer /force`, затем `gpresult /scope computer /r`.
   Убедиться, что `TEST-DeviceVPN-PreLogon` пришла. Этот подготовительный
   вызов нужен, чтобы настройки ожидания и startup script уже были локально
   известны **до** проверяемой загрузки. Его результат не засчитывается как
   доказательство pre-logon обработки.
5. Убедиться, что физическая сеть доступна до входа в Windows: Ethernet или
   сохранённый Wi-Fi-профиль для всего компьютера без captive portal.
   Пользовательский Wi-Fi, который поднимается только после входа, не
   обеспечит соединение VPN до логина.

## 2. Холодная загрузка без входа пользователя

1. Зафиксировать время, перезагрузить ПК и оставить его на экране входа.
2. На `spb-vpn-srv` убедиться, что `AL-TEST.aurora-logistics.local` появился в
   `/var/log/openvpn-status/openvpn-device-status.log` с адресом
   `10.253.91.x` **до** входа пользователя. В журнале OpenVPN проверить время
   `PUSH_REPLY` и отсутствие TLS/CRL-ошибок. Подключиться по SSH к
   `a.kuznetsov@10.78.4.253` и выполнить:

```bash
sudo systemctl is-active openvpn@server-device
sudo head -15 /var/log/openvpn-status/openvpn-device-status.log
sudo grep -F 'AL-TEST.aurora-logistics.local' /var/log/openvpn-device.log | tail -15
sudo iptables -nvL INPUT
sudo iptables -nvL FORWARD
```

   У правил для нового пула должны увеличиваться счётчики DNS и DC; другие
   назначения должны попадать в `DROP`.
3. Через RMM, запущенный от `SYSTEM`, проверить на ПК:

```powershell
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$boot
Get-Item 'C:\ProgramData\Aurora\VpnPilot\startup.txt' -ErrorAction SilentlyContinue |
    Select-Object LastWriteTime, Length
Get-Content 'C:\ProgramData\Aurora\VpnPilot\startup.txt' -ErrorAction SilentlyContinue
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

Файл `startup.txt` должен иметь дату **после** `$boot`, содержать
`NT AUTHORITY\SYSTEM`, адрес `10.253.91.x`, `SITE-SPB-DC`, доступный DC и
`True` для SYSVOL. Сравнить время его `START` с подключением OpenVPN и
событиями GroupPolicy. `gpupdate /force` после входа пользователя не доказывает
обработку политики при загрузке. Если туннель поднимается после стартовой
обработки, нужен отдельный повторный запуск компьютерной политики после
проверки DC/SYSVOL; расширения, которым нужен синхронный старт, проверить на
следующей загрузке.

## 3. Проверить AD и сертификат

- На DC1 в PowerShell выполнить `Get-ADReplicationSubnet -Identity
  '10.253.91.0/24' | Format-List Name,Site,Location`, затем
  `nltest /dsaddresstosite:10.253.91.3` и
  `nltest /server:DC2 /dsaddresstosite:10.253.91.3`. Оба DC уже возвращали
  `SITE-SPB-DC` и точную сеть `10.253.91.0/24`.
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

Если VPN не появился до входа, проверять физическую сеть, `OpenVPNService`,
профиль `config-auto\device.ovpn`, лог `device.log`, сертификат и ACL ключа.
Если VPN есть, но startup-файл отсутствует, проверять доступ к DC/SYSVOL,
время установки туннеля относительно GroupPolicy/Operational и фильтрацию
пилотной GPO. Если файл есть, но `nltest`/SYSVOL в нём неуспешны, проверять
маршруты, DNS и правила сервера/AL-OBIT.
