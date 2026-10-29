# Пилот публичного сертификата Exchange: MX4

Статус: проектирование и read-only инвентаризация. Никакие сертификаты, IIS,
Exchange-службы, DNS, NAT и HAProxy в рамках этого документа ещё не менялись.

## Цель

Проверить на одном узле DAG — `SPB-MX4` (`10.78.3.63`) — полный и обратимый
цикл установки публичного сертификата для клиентских имён, прежде чем
автоматизировать развёртывание на MX3/MX4.

Целевые имена одного сертификата RSA:

- `mail.aurora-logistics.ru`;
- `autodiscover.aurora-logistics.ru`.

Сертификат выпускается централизованно на nginx (`10.78.3.1`) существующим
HTTP-01 способом Certbot. Поэтому порт 80 на MX3/MX4 не публикуется и не нужен.
Новый отдельный lineage: `exchange-mail`; существующие отдельные lineage `mail`
и `autodiscover` не удалять до завершения пилота и переключения публикации.

## Зафиксированное исходное состояние MX4 (2026-10-29)

- IIS `0.0.0.0:443`, `0.0.0.0:444` и `127.0.0.1:443` используют
  самоподписанный сертификат `CN=SPB-MX4`, thumbprint
  `7F960B5296CF049A49428B3741DDD6752C7093F6`, срок до 2031-10-02.
- Публичного сертификата с требуемыми SAN в локальном хранилище MX4 нет.
- Связь MX4 с AD и Exchange-службы AD Topology / Service Host исправны.
- Интерактивная SSH-аутентификация `AURORA-LOGISTIC\\admin-al` доступна, но
  `Get-ExchangeCertificate` из этого SSH-сеанса получает
  `ADInvalidCredentialException`. Для автоматизации нельзя опираться на такой
  сеанс: потребуется локальная запланированная задача от `SYSTEM` или
  специально подготовленная служебная доменная учётная запись.
- Проверка через QEMU Guest Agent показала, что Exchange Management Shell
  работает от `NT AUTHORITY\\SYSTEM`. Guest Agent использовался только для
  read-only инвентаризации и **не входит** в целевую схему доставки или
  эксплуатации сертификатов.
- У текущего self-signed сертификата назначены `IIS, IMAP, POP, SMTP`.

## Зафиксированное исходное состояние nginx (2026-10-29)

- VM112 nginx доступна штатно через QEMU Guest Agent PVE2; SSH к ней не
  публикуется и не должен открываться ради автоматизации.
- Установлен Certbot `1.21.0`. Обновление Certbot должно быть отдельной
  подготовительной работой с проверкой всех существующих renewal-конфигураций;
  его нельзя совмещать с испытанием MX4.
- `http://mail.aurora-logistics.ru/.well-known/acme-challenge/*` и
  `http://autodiscover.aurora-logistics.ru/.well-known/acme-challenge/*`
  локально возвращают `301` на HTTPS. ACME HTTP-01 допускает follow redirect;
  существующие сертификаты обоих имён уже успешно обслуживаются этим nginx.
- Существуют отдельные Certbot lineage `mail.aurora-logistics.ru` и
  `autodiscover.aurora-logistics.ru`. Новый lineage `exchange-mail` не должен
  их перезаписывать или удалять.

## Границы пилота

1. Сначала выпустить staging-сертификат Let’s Encrypt для проверки HTTP-01 и
   SAN. Он не импортируется в Exchange.
2. Затем выпустить production `exchange-mail`, сформировать защищённый PFX и
   вручную доставить **только на MX4** в закрытый временный каталог.
3. Проверить импорт и содержимое PFX без привязки сервисов.
4. В окно работ включить новый сертификат на MX4 для `IIS,IMAP`. SMTP не
   переключать в этом шаге: внутренний self-signed сертификат Exchange может
   требоваться транспортным компонентам. Решение по SMTP принимается отдельно
   после аудита Receive/Send Connector, `Fqdn` и `TlsCertificateName`.
5. Провести функциональные проверки. При любой проблеме вернуть сохранённый
   thumbprint IIS и удалить только новый тестовый сертификат после проверки,
   что он больше не используется.

HAProxy, KSMG, внешний NAT/DNS и MX3 во время пилота остаются неизменными.
Следовательно, пилот не меняет внешний маршрут пользовательского трафика.

### Результат аудита SMTP MX4

Все Receive Connector (`25`, `465`, `587`, `2525`, `717`) имеют пустой
`TlsCertificateName`; четыре Send Connector также не задают
`TlsCertificateName`, и у них `RequireTLS=False`. Это подтверждает, что
публичный сертификат не следует назначать SMTP в пилоте. Отдельная работа по
SMTP потребуется только перед публикацией 587/25 через HAProxy и после
согласования имени, которое Exchange объявляет партнёрам в STARTTLS.

## Критерии готовности

- ключ RSA, закрытый ключ присутствует на MX4;
- SAN содержит ровно оба целевых имени, цепочка доверена Windows-клиентом;
- `https://mail.aurora-logistics.ru/mapi/healthcheck.htm` и Autodiscover
  проходят с ожидаемым сертификатом при контролируемом тестовом маршруте;
- OWA/ECP, MAPI/HTTP, EWS, OAB и ActiveSync проверены тестовой учётной записью;
- SMTP-поток и DAG не деградировали;
- записаны новый thumbprint, время смены и успешный откатный сценарий.

## Целевая автоматизация после пилота

`certbot deploy-hook` на nginx создаёт PFX из `exchange-mail`, проверяет SAN,
срок и SHA-256 и публикует пакет с манифестом на отдельном **внутреннем**
HTTPS endpoint nginx. Он не имеет внешнего NAT и доступен только MX3/MX4.

На каждом Exchange-сервере независимая локальная Windows Scheduled Task от
`NT AUTHORITY\\SYSTEM` по расписанию запрашивает пакет, проверяет версию, SAN
и SHA-256, импортирует сертификат и применяет утверждённый набор служб
последовательно: сначала MX4, после проверок MX3. Рабочий контур состоит
только из nginx и соответствующего MX; PVE/QEMU Guest Agent в нём не нужны.

Для endpoint применить взаимную TLS-аутентификацию: nginx принимает только
выделенные клиентские сертификаты MX3/MX4, выпущенные внутренним CA, и
проверяет их issuer/subject. Закрытый ключ PFX хранится на nginx с правами
root; пароль PFX на MX хранится локально, зашифрованный DPAPI machine context.
Ни пароль, ни ключи, ни PFX не хранятся в Git, не попадают в лог и не
передаются в аргументах процессов.

## Откат пилота

До активации сохранить действующий thumbprint и IIS bindings. При откате
вернуть `7F960B5296CF049A49428B3741DDD6752C7093F6` на IIS; перезапустить только
необходимые IIS-службы в согласованное окно; проверить `/mapi/healthcheck.htm`.
Новый сертификат не удалять, пока привязки и службы не подтверждены как
возвращённые к прежнему состоянию.

## Источники

- Let’s Encrypt: HTTP-01 и DNS-01 challenge — https://letsencrypt.org/docs/challenge-types/
- Microsoft: сертификаты Exchange — https://learn.microsoft.com/en-us/exchange/architecture/client-access/certificates
- Microsoft: импорт сертификата — https://learn.microsoft.com/en-us/exchange/architecture/client-access/import-certificates?view=exchserver-2019
- Microsoft: выбор сертификата для inbound STARTTLS — https://learn.microsoft.com/en-us/exchange/mail-flow/mail-routing/inbound-starttls-certificates-selection
