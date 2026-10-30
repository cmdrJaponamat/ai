# MX4: контрольное принудительное продление production-сертификата

Дата: 2026-10-30, около 15:18 МСК. Узел SPB-MX4 (`10.78.3.63`). По
прямому запросу владельца тест выполнен сейчас, вне обычного окна 03–04 МСК,
пока MX4 не нагружен. MX3, KSMG, nginx, HAProxy не менялись.

## До запуска

- NIC.RU `status`: refresh/GET records OK, неопубликованных изменений нет.
- Снимок под SYSTEM:
  `C:\ProgramData\AuroraNicAcme\mx4-forced-renewal-20261030-before.json`.
  Frontend IIS 443, IMAP 993, SMTP STARTTLS 25/587 предъявляли cert
  `8B11A3CD1C07AF69150EC1A88A4DEE7BBAE57679`. Все пять проверенных
  служб работали, внутренний transport cert был
  `7F960B5296CF049A49428B3741DDD6752C7093F6`, backend IIS 444 — на нём.
- MX3 был доступен на четырёх клиентских портах.

## Действие

Одноразовая задача под SYSTEM вызвала win-acme 2.2.9.1701 для renewal
`mx4-mail-production` с `--renew --id mx4-mail-production --force --nocache
--notaskscheduler`. Сценарии PowerShell перед запуском проверены парсером 5.1
с диска MX4: ошибок 0. Кэш cert/order не использовался. Все три DNS-01
авторизации для `autodiscover`, `exchange` и `mail` стали `valid`; TXT
удалены hook. Выдан cert
`AF35C0A71E7102A80A3C4A2B03D9516A9133EBE6`, срок до
2027-01-28 14:19:54 МСК. win-acme сохранил его в `LocalMachine\My` и
вызвал `install-mx4-exchange-certificate.cmd`; в
`C:\ProgramData\AuroraNicAcme\exchange-install.log` записано успешное
переключение старого thumbprint на новый. Exit code win-acme и одноразовой
задачи: 0. Одноразовая задача после проверки удалена. Ночное обычное
задание не менялось.

## Проверка после

- Снимок под SYSTEM:
  `C:\ProgramData\AuroraNicAcme\mx4-forced-renewal-20261030-after.json`.
  IIS 443 (оба frontend binding), IMAP 993, SMTP STARTTLS 25/587 предъявляют
  новый cert. Внешний OpenSSL подтверждает доверенную цепочку (`Verify return
  code: 0`) на каждом из четырёх портов. OWA/ECP без входа отвечают 302,
  MAPI/Autodiscover/EWS — 401, curl TLS verification 0.
- На 587 после STARTTLS Exchange объявляет `AUTH GSSAPI NTLM LOGIN`; IMAP
  993 возвращает `CAPABILITY` и корректный `LOGOUT`. Учетные данные и
  фактическую отправку письма в этом тесте не использовали.
- Новый cert имеет service assignment `IMAP, IIS, SMTP`. Все пять проверенных
  служб Running. Transport thumbprint `7F960B...`, backend IIS 444 и backend
  Receive Connectors 2525/465 не изменились. Frontend Receive Connectors
  25/717/587 сохранили корректный TLSCertificateName.
- NIC.RU `status` OK, `StateCount=0`, zone clean. win-acme видит production
  renewal с двумя успешными выпусками и due после 2026-12-24; обычное
  задание под SYSTEM на 03:00 МСК осталось с LastTaskResult=0.
- Отрицательная проверка: установочный сценарий получил staging thumbprint
  `6862DE...`, отверг его до изменения служб (`TaskResult=1`, лог
  `Unexpected new certificate subject or issuer`). Четыре порта продолжили
  отдавать новый production cert.

## Восстановление и остаточный риск

Оба production cert сохранены в LocalMachine My; не удалять их без сверки
фактических bindings и WACS cache. Отдельный полный живой откат не выполнен:
при одинаковых issuer/subject Exchange может выбирать более новый cert для
SMTP, поэтому простой возврат `TlsCertificateName` не гарантирует откат
thumbprint. Скрипт пытается восстановить старые настройки при ошибке и
выходит с ошибкой; после любой такой ошибки нужна ручная проверка 443/993/
25/587 и `exchange-install.log`. Прежний self-signed internal transport cert
не менять. Снимки before/after — точные контрольные значения.

Restart/reboot: при успешном переключении скрипт кратко перезапустил только
MSExchangeIMAP4BE и MSExchangeIMAP4; reboot не выполнялся.
