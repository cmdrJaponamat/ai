# 2026-10-30 — тайм-аут ActiveSync на внешнем nginx

## Проблема и факты

- Для `a.prudovskii` мобильное приложение сообщает неопределённую ошибку проверки подлинности.
- Внешний nginx (VM112 на PVE2) направляет `mail.aurora-logistics.ru` на MX3 `10.78.3.62:443`.
- На `POST /Microsoft-Server-ActiveSync?...Cmd=Ping` у iPhone `a.prudovskii` есть повторяющиеся `upstream timed out (110)`; последний подтверждённый до правки — 30.10.2026 09:47:59 MSK.
- `proxy_read_timeout` на уровне виртуального хоста — 360 секунд. Отдельного тайм-аута для ActiveSync нет.
- При этом Outlook Mobile ранее получал HTTP 200 на `Sync`, `ItemOperations` и `Settings`. Поэтому изменение тайм-аута — проверка гипотезы об обрыве долгих запросов, а не доказанное решение ошибки интерфейса Outlook.

## Выполненное изменение

- Файл: `/etc/nginx/conf.d/mail.aurora-logistics.ru.conf` на VM112.
- В `location ~* ^/Microsoft-Server-ActiveSync` добавлены `proxy_read_timeout 1800s;` и `proxy_send_timeout 1800s;`; общий тайм-аут остальных маршрутов остался 360 секунд.
- До правки создана копия с суффиксом `.pre-activesync-timeout-20261030`. Затем успешно выполнены `nginx -t` и `systemctl reload nginx`.

## Откат

- Восстановить файл из `/etc/nginx/conf.d/mail.aurora-logistics.ru.conf.pre-activesync-timeout-20261030`, выполнить `nginx -t`, `systemctl reload nginx`.
- Перезагрузка VM не требуется. Требуется только reload nginx.

## Проверка и дальнейшее наблюдение

- 30.10.2026 10:13 MSK: `nginx -t` — успешно, `systemctl is-active nginx` — `active`.
- Тест без учётных данных через этот виртуальный хост на `127.0.0.1` вернул ожидаемый HTTP 401 за 0,013 секунды: маршрут отвечает и требует авторизацию.
- Последующая попытка подключения и выводы приведены ниже. Исчезновение `Ping` timeout у iPhone можно подтвердить только после следующего долгого опроса.

## Результат повторной попытки и диагностика Exchange

- Пользователь повторил добавление ящика в Outlook Mobile: сообщение об ошибке проверки подлинности осталось. Значит, повышение тайм-аута не устранило эту ошибку.
- 30.10.2026 около 10:14–10:20 МСК: на MX3 `HttpProxy/Eas` для Outlook DeviceId `a6b0ff1131284c838295df04c6740414` показал `Basic=true`, `AURORA-LOGISTIC\a.prudovskii`, маршрутизацию на MX4, HTTP 200. Начальные 401 сопровождались успешным повтором с учётными данными.
- На MX4 backend IIS для того же устройства: `SC1:1` (успех протокола), `As:AllowedG`, `Throttle:0`, HTTP 200. `Get-MobileDeviceStatistics`: `DeviceOk`, `Allowed`, `LastSuccessSync=30.10.2026 07:20:58 UTC`. Первое подключение данного партнёрства — 02.06.2025; отдельного нового устройства после попытки не появилось.
- Публичный Autodiscover V2 `Protocol=ActiveSync` для этого адреса возвращает HTTP 200 и корректный URL `https://mail.aurora-logistics.ru/Microsoft-Server-ActiveSync`.
- Отдельная ошибка конфигурации: на обоих Exchange пустой `ExternalUrl` Autodiscover; запросы `Protocol=AutodiscoverV1` для других пользователей возвращают HTTP 500, а MX4 пишет MSExchange Autodiscover Event ID 1 (`GetHostNameFromVdir`). Для запроса `a.prudovskii` с `Protocol=ActiveSync` эта ошибка не наблюдалась. Исправление Autodiscover требует отдельного изменения.
- На MX4 также есть Event ID 4999 для `MSExchangeSyncAppPool` с `EntityContentProperty.get_MIMEData`; прямой связи с сеансом `a.prudovskii` в доступных записях нет.
- На этом этапе было решено проверить ручной ввод домена при добавлении Exchange-учётной записи.

## Итог 30.10.2026 10:28 МСК

- Пользователь подтвердил успешное добавление ящика в Outlook Mobile после замены домена в отдельном поле приложения: вместо DNS-имени AD `aurora-logistics.local` указано короткое имя `AURORA-LOGISTIC`; имя пользователя — `a.prudovskii`.
- `Get-MobileDeviceStatistics` на MX4 подтвердил новое устройство Outlook `522b742ce9584d07b1f259d7c49e2f48`: `FirstSyncTime=30.10.2026 07:27:14 UTC`, `LastSuccessSync=07:28:13 UTC`, `DeviceAccessState=Allowed`, `Status=DeviceOk`.
- После замены значения поля «Домен» добавление прошло успешно. Это не доказывает, что DNS-имя домена не поддерживается сервером: вывод ниже уточняет причину. Повышение тайм-аута nginx не исправляло ошибку добавления; оно оставлено для отдельно обнаруженных обрывов долгих `Ping` у iPhone. Ошибки Autodiscover V1 остаются отдельной задачей.

## Уточнение после вопроса пользователя

- Старое партнёрство Outlook `50d3c0b36b33406682e4b74f99bbbb55` **30.10.2026 в 05:40:46 МСК** получило HTTP 200 с именем `aurora-logistics.local\a.prudovskii`. Значит, Exchange и сейчас принимает длинное DNS-имя в уже работающем сеансе. В тот же день другие Outlook-устройства с таким форматом тоже получали HTTP 200.
- Во время неудачных попыток после 09:00 МСК nginx не зафиксировал ни одного запроса ActiveSync с `User=aurora-logistics.local\a.prudovskii`. Нельзя доказать по серверным журналам, какую именно строку приложение передало при регистрации и на каком клиентском шаге возникла ошибка.
- Новое партнёрство появилось после ввода короткого домена: первый запрос с `User=aurora-logistic\a.prudovskii` пришёл в 10:27:13 и успешно завершился HTTP 200.
- Документация Microsoft для настройки Outlook Mobile с Basic Auth при использовании `sAMAccountName` указывает NetBIOS-имя в поле `Account domain`: https://learn.microsoft.com/en-us/exchange/clients/outlook-for-ios-and-android/account-setup?view=exchserver-2019 . Это объясняет, почему короткий формат надёжен для новой настройки, но не доказывает, почему прежняя настройка с длинным форматом работала и почему текущая попытка не прошла.
