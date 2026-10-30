# MX4: production-сертификат Let’s Encrypt для Exchange

Дата: 2026-10-30. Узел: SPB-MX4 (`10.78.3.63`). MX3, nginx и HAProxy не менялись.

## Что сделано

- Под SYSTEM одноразовым локальным Scheduled Task снят полный preflight:
  `C:\ProgramData\AuroraNicAcme\mx4-production-preflight-20261030.json`.
  Такой же postflight в `mx4-production-postflight-20261030.txt`. Задания
  после выполнения удалены; PVE Guest Agent и WinRM не использовались.
- win-acme 2.2.9.1701 через NIC.RU DNS-01 выпустил production-сертификат
  `8B11A3CD1C07AF69150EC1A88A4DEE7BBAE57679` для `mail`,
  `autodiscover`, `exchange.aurora-logistics.ru`, срок до
  2027-01-28 13:38:58 МСК. Renewal ID `mx4-mail-production`, данные в
  `C:\ProgramData\AuroraNicAcme\wacs-staging-data`. При первом выпуске
  использовался install plugin `none` и без Scheduled Task.
- В Exchange сертификат назначен IIS, SMTP, IMAP. При назначении SMTP на
  вопрос о замене внутреннего транспортного сертификата дан ответ `No`.
  `InternalTransportCertificateThumbprint` остался
  `7F960B5296CF049A49428B3741DDD6752C7093F6`. Frontend Receive
  Connectors 25/717/587 используют `<I>CN=YR1, O=Let's Encrypt, C=US` +
  `<S>CN=mail.aurora-logistics.ru`; только Client Frontend 587 имеет FQDN
  `mail.aurora-logistics.ru`. Backend 2525/465 не трогали.
- Frontend IIS `:443:` и `127.0.0.1:443:` используют новый сертификат;
  Exchange Back End `*:444:` оставлен на старом self-signed. IMAP
  `X509CertificateName=mail.aurora-logistics.ru`; службы
  `MSExchangeIMAP4BE` и `MSExchangeIMAP4` были кратко перезапущены.
- После отдельной ошибки удаления ACME TXT запись NIC.RU ID `70596688`
  `_acme-challenge.exchange` сверена по ID/имени/значению и удалена только
  она. Локальный state пуст, неопубликованных правок зоны нет. Исправлена
  обработка исключения без `ErrorDetails` в `NicAcme.Common.ps1`, с
  предварительным backup на MX4
  `C:\ProgramData\AuroraNicAcme\NicAcme.Common.pre-errorhandling-20261030.ps1`.

## Проверка

- Прямо с рабочего ПК 443, 993, 25/STARTTLS и 587/STARTTLS предъявляют
  один thumbprint `8B11A3CD...`, корректную цепочку Let’s Encrypt.
- OWA/ECP без входа: HTTP 302; MAPI/Autodiscover/EWS без входа: HTTP 401;
  TLS verification у curl: 0.
- Postflight: все пять служб Running, внутренний транспортный thumbprint
  неизменён, Backend IIS 444 неизменён. Первое действие IMAP-шага
  остановилось защитной проверкой: `Enable-ExchangeCertificate` уже сам
  поменял X509CertificateName. Повторный шаг это учёл и перезапустил службы.

## Восстановление / ограничения

Новый cert не удалять и не отменять renewal, пока не подтверждено, какие
привязки реально используют его. При проблеме сверить два сохранённых
снимка; возвращать только Frontend IIS 443, три Frontend Receive Connectors
и IMAP. Backend 444 и внутренний транспортный сертификат не менять.
Прежний self-signed cert физически остаётся в LocalMachine My.

Позже в тот же день подключён локальный install script
`C:\ProgramData\AuroraNicAcme\install-mx4-exchange-certificate.cmd` с
`{CertThumbprint}`. Предыдущие settings/renewal JSON сохранены с суффиксом
`.pre-automation-20261030`; task под SYSTEM создан на 03:00 МСК ежедневно,
без random delay, лимит 1 час. Его ручной контрольный запуск завершился 0:
сертификат ещё не due (после 2026-12-24), нового выпуска/перезапуска нет.
No-op ветка install script на текущем сертификате также завершилась 0 и
проверила TLS 443/993/25/587. **Фактическое автоматическое обновление с
новым thumbprint ещё не проверено**, поскольку пользователь согласовал
окно 03:00–04:00 МСК и принудительный выпуск вне окна не выполнялся.
При ошибке установки скрипт пытается вернуть прежние привязки, но откат
SMTP при совпадающем issuer/subject двух cert не гарантирован; проверять
внешние порты и журнал `exchange-install.log` вручную. Staging renewal не
включать.

Relogin/reboot: нет. Restart: только две IMAP-службы. Подробности:
`/home/admin-al/assistant/notes/projects/aurora-logistics-mail/exchange-certificate-automation/MX4-PILOT-RUNBOOK.md`.
