# MX4: win-acme staging через NIC.RU DNS-01

Дата: 2026-10-30. Узел: SPB-MX4 (`10.78.3.63`).

## Задача и исходное состояние

Проверить полный ACME DNS-01 цикл на MX4 без назначения сертификата
Exchange-службам. Старый `C:\Didtr\exchange server 2019\wacs\wacs.exe`
версии 2.1.20.1185 имел пустой `--list`, Scheduled Task отсутствовал,
`Script.Timeout=600`. NIC.RU hook уже прошёл DNS-only тест.

## Изменения

- Официальный win-acme 2.2.9.1701 x64 pluggable размещён отдельно в
  `C:\ProgramData\AuroraNicAcme\wacs-2.2.9.1701-staging`, с данными в
  `C:\ProgramData\AuroraNicAcme\wacs-staging-data`. Старый каталог не менялся.
  ZIP SHA-256: `A2C874E9893A1D91E0329887F72C067DCC49800A49963FA7D61C5A4E09058F0C`.
  EXE SHA-256: `64407D4E4A1BCD7C33006399D813AD8F569BFFE79756D398480F1FD3A803DA61`.
- В отдельном `settings.json`: `Script.Timeout=1800`,
  `Validation.DnsServers=[1.1.1.1]`, `Installation.DefaultInstallation=none`,
  отдельный `Client.ConfigurationPath`. Корневой каталог доступен только
  SYSTEM/Administrators.
- Создан тестовый ACME renewal `mx4-nic-staging-20261030` через DNS Script
  с последовательными TXT для трёх SAN. Тестовый сертификат Let's Encrypt
  staging сохранён в LocalMachine `My`, thumbprint
  `6862DE0407A314D6C49A776B68F8AEB71D66857E`. Установка: plugin `none`.
  Scheduled Task не создавался. MX3 не трогали.

## Проверка и ограничения

- CA подтвердила `autodiscover`, `exchange`, `mail`; каждый TXT удалён hook.
  NIC.RU API: `has-changes=false`, локальных `record-*.json` нет; среди
  challenge-записей осталась только ранее существовавшая
  `_acme-challenge.telematika`.
- Сертификат содержит три требуемых SAN и закрытый ключ. На 443, 993,
  25/STARTTLS и 587/STARTTLS MX4 всё ещё предъявляет прежний self-signed
  `CN=SPB-MX4`, thumbprint `7F960B5296CF049A49428B3741DDD6752C7093F6`.
  `Get-ExchangeCertificate` из SSH-сеанса не прошёл AD-аутентификацию;
  отсутствие назначения подтверждено внешним TLS и plugin `none`.
- Подпись нового EXE в Windows имеет статус `UnknownError`: подписант
  `CN=WACS` истёк 2026-02-02; старый EXE показывает тот же статус.
  Поэтому подпись не зачтена как успешная проверка. Пакет скачан по HTTPS
  из официального GitHub Release, ZIP и EXE сверены по SHA-256.
- Первый неинтерактивный `--test` прошёл DNS-01, но остановился на вопросе
  о сохранении сертификата. Интерактивный повтор сохранил сертификат и
  renewal; затем win-acme упал при восстановлении кодировки SSH-консоли
  (`ConsolePal.SetConsoleOutputEncoding`). Несмотря на код выхода, выпуск
  проверен отдельно. Повторять заказ только ради кода выхода не нужно.

## Откат и продолжение

Сейчас откат рабочих служб не требуется: привязки не менялись. Если нужно
удалить пилот, сначала точечно убедиться, что staging-сертификат не назначен
службам, затем отменить только renewal `mx4-nic-staging-20261030` и удалить
только сертификат с указанным thumbprint; отдельный каталог win-acme можно
оставить до production-перехода. Не удалять весь `AuroraNicAcme`: там
рабочий NIC.RU hook и DPAPI config.

Следующее рабочее окно: снять точный срез сертификатов, IIS bindings и
SMTP-коннекторов; создать production renewal, настроить выбор SMTP-сертификата,
назначить IIS/SMTP/IMAP и проверить 443/993/25/587. Тестовый сертификат
недоверенный и не должен попасть в службы.

Relogin/restart/reboot: не требовались и не выполнялись.
Подробный runbook: `/home/admin-al/assistant/notes/projects/aurora-logistics-mail/exchange-certificate-automation/MX4-PILOT-RUNBOOK.md`.
