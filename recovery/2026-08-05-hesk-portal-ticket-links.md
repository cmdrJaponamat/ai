# HESK: ссылки из писем на карточки PortalAL

Дата: 2026-08-05

## Что сделано

- PortalAL получил динамический маршрут `/requests/<track-id>`.
- Страница запрашивает заявку через существующий endpoint «мои заявки»: сервер сопоставляет e-mail HESK с e-mail текущей AD-сессии. Сам номер заявки в URL не предоставляет доступ.
- В HESK переключены только пользовательские шаблоны `new_ticket`, `new_ticket_by_staff`, `new_reply_by_staff`, `ticket_closed`, в обычном и HTML-виде. На период проверки каждый из них содержит две ссылки: сначала карточку PortalAL, ниже — малозаметный резервный переход в HESK. Ссылки исполнителям не менялись и продолжают вести в административный HESK.
- В прямой карточке PortalAL добавлены пользовательские действия HESK: ответ с вложениями, скачивание/просмотр вложений, закрытие, возобновление, печать и оценка ответа исполнителя. Оценка включена в HESK и сохраняется в его исходных таблицах.

## Фактическое состояние

- Портал: образ `portal-al:132aee1`, health-check успешен.
- Шаблоны HESK: `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/{emails,html_emails}/`.
- Резервные копии: исходная до первого переключения `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921`; перед добавлением обеих ссылок — `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-115408`; перед сменой их приоритета — `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-115929`.
- Мост HESK: `/opt/hesk-portal-bridge/index.php`; резервная копия перед добавлением оценки ответа — файл с суффиксом `.bak-20260805-1154*` в том же каталоге.
- Исходник безопасного применения: `assistant/apps/internal-employee-portal/integrations/hesk-email-templates/apply-portal-ticket-links.sh`.

## Откат

```bash
sudo cp -a /var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921/emails/. /var/www/helpdesk.aurora-logistics.ru/html/language/ru/emails/
sudo cp -a /var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921/html_emails/. /var/www/helpdesk.aurora-logistics.ru/html/language/ru/html_emails/
```

Если нужен полный откат интерфейса, развернуть предшествующий образ PortalAL. Перезагрузка HESK, nginx или браузера не требуется.

Для отката только новых действий requester UI: развернуть образ `portal-al:fc38e65` и восстановить предыдущий `/opt/hesk-portal-bridge/index.php.bak-20260805-1154*`. Это уберёт действия «Оценить ответ», «Закрыть» и «Возобновить» с прямой карточки, но не изменит сами заявки.

Прямая страница `/requests/<track-id>` автоматически обновляет данные каждые 20 секунд, только пока вкладка видима, и сразу после возвращения фокуса. Обновление не меняет черновик ответа и выбранные файлы. Откат: развернуть образ `portal-al:be440e2`.

Операторские уведомления HESK (`category_moved`, `new_note`, `new_reply_by_customer`, `new_ticket_staff`, `overdue_ticket`, `ticket_assigned_to_you`, `ticket_escalated`) теперь сначала ведут на `/tickets?ticket=<track-id>`, затем содержат резервную ссылку HESK. Портал допускает к этой карточке только пользователя с ролью `it`/`admin`, связанным профилем HESK, правом просмотра и категорией заявки. История HESK (создание, назначение, смены статуса, категории, приоритета, сроков, вложений и системные события) видна и заявителю, и исполнителю; внутренние заметки остаются только у исполнителя.

Для исполнителя история дополнительно раскрыта в правой панели «Действия», поэтому длинное описание больше не вытесняет её за нижнюю границу карточки. Для заявителя журнал расположен первым блоком карточки.
