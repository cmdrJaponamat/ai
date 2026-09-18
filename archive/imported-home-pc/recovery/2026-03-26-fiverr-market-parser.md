# Fiverr Market Parser

## Проблема

Нужно было сделать не просто заметку, а реальный парсер, который формирует Markdown/CSV-отчёт для выбора подработки на Fiverr по текущему профилю, навыкам и интересам пользователя.

## Что найдено

- Прямой HTML-поиск Fiverr и прямой доступ к gig-страницам для анонимного клиента часто упираются в `403`
- У Fiverr есть публичный источник для обхода этой проблемы:
  - `https://www.fiverr.com/sitemap_gigs.xml.gz`
- Основной рабочий путь:
  1. получить список gig sitemap-ов
  2. пройтись по URL gig’ов
  3. ранжировать их по ключам из профиля
  4. вывести отчёт в `md` и `csv`

## Изменения

Созданы файлы:

- `/home/japonamat/fiverr_market_parser.py`
- `/home/japonamat/fiverr_market_report.md`
- `/home/japonamat/fiverr_market_report.csv`

Скрипт:

- использует публичные Fiverr sitemap’ы
- не зависит от авторизованной сессии
- группирует найденные gig’и по 6 трекам:
  - Python scripts and automation
  - Bash / PowerShell scripting
  - Small bug fixing
  - Small Node.js backend tasks
  - C++ tools and technical prototypes
  - Small gamedev technical tasks
- оценивает `fit`, `difficulty`, `risk`, `english_load`, `portfolio_dependency`
- добавляет ориентировочные стартовые ценовые диапазоны
- сохраняет отчёт в Markdown и CSV

## Проверка

- Скрипт успешно выполнен локально
- Выходные файлы созданы
- Отчёт просмотрен вручную
- В отчёте есть реальные публичные Fiverr gig URLs, сгруппированные по нужным направлениям

## Ограничения

- Это не полноценный парсер внутренних Fiverr search results
- Реальные цены с gig-страниц не спарсятся из-за антибот-ограничений
- Поле `estimated_starter_price` основано на рыночной эвристике для нового профиля, а не на live scraping
- Некоторые направления пока дают шум, например `bug fixing` может подтягивать много WordPress-задач; это нужно дальше поджимать фильтрами

## Откат

- Удалить:
  - `/home/japonamat/fiverr_market_parser.py`
  - `/home/japonamat/fiverr_market_report.md`
  - `/home/japonamat/fiverr_market_report.csv`
- Либо отредактировать keyword tracks внутри скрипта под другую стратегию

## Нужен ли relogin/reboot

Нет
