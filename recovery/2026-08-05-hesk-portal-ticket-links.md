# HESK: ссылки из писем на карточки PortalAL

Дата: 2026-08-05

## Что сделано

- PortalAL получил динамический маршрут `/requests/<track-id>`.
- Страница запрашивает заявку через существующий endpoint «мои заявки»: сервер сопоставляет e-mail HESK с e-mail текущей AD-сессии. Сам номер заявки в URL не предоставляет доступ.
- В HESK переключены только пользовательские шаблоны `new_ticket`, `new_ticket_by_staff`, `new_reply_by_staff`, `ticket_closed`, в обычном и HTML-виде. Ссылки исполнителям не менялись и продолжают вести в административный HESK.

## Фактическое состояние

- Портал: образ `portal-al:fc38e65`, health-check успешен.
- Шаблоны HESK: `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/{emails,html_emails}/`.
- Резервная копия до замены: `/var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921`.
- Исходник безопасного применения: `assistant/apps/internal-employee-portal/integrations/hesk-email-templates/apply-portal-ticket-links.sh`.

## Откат

```bash
sudo cp -a /var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921/emails/. /var/www/helpdesk.aurora-logistics.ru/html/language/ru/emails/
sudo cp -a /var/www/helpdesk.aurora-logistics.ru/html/language/ru/.portal-ticket-links-20260805-103921/html_emails/. /var/www/helpdesk.aurora-logistics.ru/html/language/ru/html_emails/
```

Если нужен полный откат интерфейса, развернуть предшествующий образ PortalAL. Перезагрузка HESK, nginx или браузера не требуется.
