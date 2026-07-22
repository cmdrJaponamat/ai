# Wiki.js: выравнивание оформления с порталом

## Задача

Сделать оформление Wiki.js визуально согласованным с внутренним порталом и
подтвердить, что тема применяется в production.

## Что было найдено

- Корпоративный CSS уже был подключен через `theming.config.injectCSS`.
- Шрифты `Cera Pro` и `Akrobat` доступны на `wiki.aurora-logistics.ru` по
  `/brand/fonts/`.
- Живая тема содержала более ранние близкие, но не идентичные токены цветов.

## Изменения

- В `assistant/notes/projects/inventory-wiki/wiki-content/aurora-wiki.css`
  базовые токены выровнены с порталом:
  - primary: `#2f5fa8`;
  - deep primary: `#1f437f`;
  - accent: `#35aa92`;
  - ink: `#101318`;
  - muted: `#5e6b7c`.
- В `apply_wiki_theme.py` добавлен режим `--check`: он read-only проверяет
  ключевые маркеры корпоративной темы в `injectCSS`.
- Обновленный CSS применен через Wiki.js GraphQL API.

## Проверка

- `python3 apply_wiki_theme.py` завершился успешно.
- `python3 apply_wiki_theme.py --check` завершился успешно.
- `https://wiki.aurora-logistics.ru/ru/it` содержит примененные primary и
  accent токены.
- `/brand/fonts/CeraPro-Regular.ttf` и `/brand/fonts/Akrobat-Bold.ttf`
  возвращают HTTP 200.

## Откат

Вернуть в `aurora-wiki.css` предыдущие значения `#2e63ae`, `#214d8c`,
`#159b8d`, `#1b2a3d`, `#63738a`, затем повторно выполнить
`python3 apply_wiki_theme.py`.

## Перезапуск

Не требуется.
