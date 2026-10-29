# Детальный проект автоматизации сертификатов Exchange

## Границы и поток

```text
Let's Encrypt
    │ HTTP-01 через существующий nginx :80
    ▼
Certbot на nginx
    │ успешное renew → deploy-hook
    ▼
PFX + manifest в закрытом каталоге nginx
    │ внутренний HTTPS, mTLS, только MX3/MX4
    ├───────────────────────────┐
    ▼                           ▼
MX4 Scheduled Task          MX3 Scheduled Task
(LocalSystem)               (LocalSystem)
    │                           │
    ▼                           ▼
Exchange Management Shell   Exchange Management Shell
```

Внешний трафик не получает доступ к каталогу распространения. PVE, QEMU Guest
Agent, SSH, WinRM и доменные пароли не требуются в рабочем цикле.

## 1. Certbot и единый lineage

На nginx создаётся отдельный RSA lineage `exchange-mail` с SAN:

- `mail.aurora-logistics.ru`;
- `autodiscover.aurora-logistics.ru`.

Существующие отдельные сертификаты nginx продолжают обслуживать текущие
vhost до отдельного переключения; новый lineage не заменяет их автоматически.
Certbot выполняется таймером, как и сейчас. Hook запускается **только** при
успешном выпуске или продлении `exchange-mail`, получает путь в
`RENEWED_LINEAGE` и завершает работу с ошибкой для любой другой линии.

До включения hook обновить Certbot отдельно и проверить все имеющиеся renewal
конфигурации, в том числе исправить повреждённую legacy-конфигурацию Directum.

## 2. Deploy-hook nginx

Hook выполняется root и делает строго следующее:

1. Проверяет, что `fullchain.pem` и `privkey.pem` принадлежат lineage
   `exchange-mail`.
2. Через OpenSSL проверяет RSA-ключ, срок действия, issuer и оба необходимых
   SAN. Если любое условие не прошло, пакет не публикуется.
3. Создаёт временный PFX: leaf + intermediate chain + private key. Пароль
   читает из root-only файла, например `/etc/exchange-cert/pfx-password`;
   не передаёт его в command line и не печатает в лог.
4. Считает SHA-256 PFX и записывает атомарный JSON-манифест: schema version,
   monotonically increasing release ID, certificate serial, SHA-256, notBefore,
   notAfter, SAN и creation timestamp. Ни PFX, ни пароль в JSON не включаются.
5. Публикует PFX и manifest как один новый immutable release-каталог,
   например `/srv/exchange-cert/releases/<serial>/`; после полной записи
   переключает атомарную ссылку `current`.
6. В журнал пишет только release ID, серийный номер и срок. Старые release
   хранятся ограниченное время (например, 30 дней) для отката.

При ошибке hook оставляет `current` прежним. Следующая задача MX увидит
предыдущий корректный release, а не частично созданный файл.

## 3. Внутренний endpoint nginx

Отдельный server block слушает только внутренний адрес nginx либо доступен
через firewall исключительно с `10.78.3.62` и `10.78.3.63`. Для него:

- нет публичного DNS/NAT и нет смешения с пользовательским `mail` vhost;
- разрешены лишь `GET /current/manifest.json` и `GET /current/exchange-mail.pfx`;
- включён `ssl_verify_client on`;
- доверен только CA, выдавший два выделенных *клиентских* сертификата MX3/MX4;
- дополнительно nginx сопоставляет Subject/SAN сертификата с разрешённым узлом;
- запрещён directory listing, методы кроме GET/HEAD, кэширование PFX и запись;
- access log не содержит query secrets; error log не содержит путей к закрытым
  ключам или содержимого заголовков.

TLS-сертификат endpoint — обычный внутренний серверный сертификат. Клиентский
сертификат endpoint не имеет отношения к публичному сертификату Exchange и
не используется Outlook.

## 4. Локальная задача Exchange

На каждом MX один и тот же PowerShell-скрипт размещён локально,
например `C:\ProgramData\Aurora\ExchangeCert\Apply-ExchangeCertificate.ps1`.
Windows Scheduled Task запускает его от `NT AUTHORITY\SYSTEM` каждые 30 минут
и после старта ОС. Задача не зависит от сети в момент запуска: при недоступном
nginx она пишет краткое событие и заканчивается успешно без изменения
текущего сертификата.

Скрипт:

1. Использует локальный client-certificate из `LocalMachine\My` для mTLS и
   скачивает manifest через HTTPS с нормальной проверкой имени и цепочки
   endpoint.
2. Валидирует JSON schema, release ID, SAN, срок годности (например, не менее
   30 дней), SHA-256 и отсутствие rollback на более старый release.
3. Если release уже применён, ничего не делает.
4. Скачивает PFX во временный каталог ACL только для SYSTEM/Administrators,
   повторно сверяет SHA-256. Пароль PFX получает из DPAPI-secret, созданного
   при первоначальной установке именно от machine context.
5. Импортирует сертификат в `LocalMachine\My`, проверяет private key, SAN,
   chain и срок, затем находит его Exchange thumbprint.
6. В режиме пилота применяет **только** `Enable-ExchangeCertificate` для
   `IIS,IMAP`; `SMTP` и `POP` остаются выключенными до отдельного решения.
   Перед включением записывает прежний thumbprint и привязки в локальный
   rollback-state.
7. Выполняет локальные HTTP/HTTPS проверки MAPI healthcheck и IMAPS handshake;
   при неуспехе сразу возвращает прежний IIS/IMAP thumbprint и помечает release
   failed, чтобы не повторять опасный цикл каждые 30 минут.
8. Удаляет временный PFX, сохраняет короткий Event Log и локальный state:
   release ID, thumbprint, время, результат и причину ошибки без секретов.

`SYSTEM` выбран не из-за PVE, а потому что это локальный, постоянно доступный
контекст Windows для задачи и хранилища сертификатов машины.

## 5. Последовательность MX4 → MX3

В manifest есть разрешённый этап: `pilot-mx4`, `rollout-mx3`, `steady-state`.
MX4 принимает `pilot-mx4`; MX3 в этом этапе только скачивает и валидирует,
но не импортирует/не применяет сертификат. После ручной проверки MX4 оператор
публикует новый release с разрешённым этапом. Тогда MX3 применяет
следующий release. Автоматизация никогда не обновляет оба узла одновременно.

На реальном HAProxy-контуре перед применением узла задача/оператор сначала
выводит этот backend из новых соединений, после проверки возвращает его в
балансировку. Пока HAProxy не введён в маршрут, это условие не используется.

## 6. Ручное управление и аварийный откат

- Задача имеет параметр `-Mode Audit`, который только скачивает и валидирует.
- `-Mode Stage` импортирует, но не включает сертификат.
- `-Mode ApplyIisImap` допустим лишь в утверждённое окно.
- `-Mode Rollback` читает локальный rollback-state, возвращает предыдущий
  thumbprint IIS/IMAP и делает локальные health checks.
- Для блокировки всей автоматики оператор создаёт локальный kill-switch файл;
  задача прекращается до сетевого запроса.

Автоматическое удаление старых сертификатов запрещено. Очистка проводится
отдельно после подтверждения, что сертификат нигде не используется.
