# Памятка новому сотруднику на внутреннем портале — 2026-11-27

## Задача и исходное состояние

Из PDF `/home/admin-al/assistant/notes/projects/internal-employee-portal/Памятка для новых сотрудников.pdf` подготовить веб-страницу на внутреннем портале. Вместо адреса старого Helpdesk указать создание ИТ-заявки через портал.

В Wiki.js уже существовала опубликованная страница `portal/start` (ID 32) с коротким черновиком от 2026-07-07. Портал показывает опубликованные страницы раздела `portal/` через проекцию Wiki.js по адресу `/instructions/portal/start`.

## Изменения

- Исходный Markdown: `/home/admin-al/assistant/notes/projects/internal-employee-portal/wiki-drafts/portal/portal__start.md`.
- Страница Wiki.js ID 32 обновлена через GraphQL API; сохранены путь `portal/start`, заголовок «Новый сотрудник», теги и публикация.
- Добавлены разделы про учётную запись, Outlook, TrueConf, 1С, КЭДО, VPN и обращение в ИТ. Прямая ссылка на заявку: `https://portal.aurora-logistics.local/requests`. Общая почта `it@aurora-logistics.ru` указана только на случай недоступности портала.
- Прежний Markdown из Wiki.js сохранён в `recovery/2026-11-27-portal-start-before.md`.
- Проекция в рабочем контейнере `portal-al` на `10.78.3.149` синхронизирована штатной функцией `syncWikiProjection()`.

## Проверка

- GraphQL Wiki.js: содержимое совпало с исходным Markdown, HTML содержит ссылку на заявки и OpenVPN GUI, старого URL Helpdesk нет.
- На сервере портала `/requests` и `/instructions/portal/start` отдают HTML с кодом 200; серверный API статей требует авторизацию, что ожидаемо.
- Проекция: `pagesTotal=15`, `pagesUpdated=1`; запись `portal/start` содержит ссылку на заявки и образец почтовой подписи, старого URL Helpdesk нет.
- Проверка в браузере под учётной записью сотрудника не выполнялась.

## Откат

Восстановить содержимое Wiki.js страницы ID 32 из `recovery/2026-11-27-portal-start-before.md` через тот же GraphQL `pages.update`, затем вызвать штатную `syncWikiProjection()`. Исходный Markdown также можно вернуть отдельным git-коммитом. Перезапуск контейнера, сервера и повторный вход пользователей не требуются.
