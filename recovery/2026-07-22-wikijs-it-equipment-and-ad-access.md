# Wiki.js: оборудование ИТ и доступ через AD

Дата: 2026-07-22

## Выполнено

- В Wiki.js опубликованы 22 страницы дерева `/it`, в том числе новый каталог:
  - `/it/equipment`;
  - `/it/equipment/data-center`;
  - `/it/equipment/network`;
  - `/it/equipment/workplaces`;
  - `/it/equipment/print`.
- В каталог попали только нормализованные сведения: количество, классы,
  модельные семейства, локации, роли и статус. Не публикуются IP/MAC,
  серийные и инвентарные номера, персональное закрепление, пароли,
  конфигурации и backup-файлы.
- Доступ к `/it` закрыт правилами Wiki.js:
  - `Guests`: `deny-it-knowledge-guests`, `START it`, deny;
  - `ldap-users`: `deny-it-knowledge`, `START it`, deny;
  - `Role-IT`: `allow-it-knowledge`, `REGEX ^it$|^it/`, allow.
- Более специфичное `REGEX`-правило `Role-IT` имеет приоритет над общим
  `START` deny для пользователей, состоящих в обеих LDAP-группах. Это
  подтверждено реализацией Wiki.js 2.5.307 в `/opt/wiki/server/core/auth.js`.
- Скрипт `/opt/portal-al/scripts/sync-wiki-it-access.mjs` развёрнут в образе
  `portal-al`. Он фильтрует отключённые учётные записи и использует AD
  matching-rule-in-chain для вложенных членств.
- В production `.env` добавлены Wiki API variables; перед изменением создана
  копия `/opt/portal-al/.env.backup.wiki-it-access-20260722`.
- На `spb-wiki` включены:
  `/etc/systemd/system/portal-wiki-it-access.service` и
  `/etc/systemd/system/portal-wiki-it-access.timer`.
  Таймер запускает синхронизацию каждые 15 минут.

## Проверки

- Контейнер `portal-al` healthy после rebuild.
- Последний запуск sync: 5 AD-участников, изменений ролей и членства не
  потребовалось.
- Анонимный GraphQL-запрос страницы `/it` получил `PageViewForbidden 6013`.
- `portal-wiki-it-access.service` завершился с `status=0/SUCCESS`; timer active.

## Откат

1. `sudo systemctl disable --now portal-wiki-it-access.timer` на `spb-wiki`.
2. Удалить два unit-файла, выполнить `sudo systemctl daemon-reload`.
3. Восстановить `/opt/portal-al/.env` из
   `/opt/portal-al/.env.backup.wiki-it-access-20260722`, затем пересобрать
   `/opt/portal-al` через `docker compose up --build -d portal`.
4. Через Wiki.js GraphQL удалить два deny-правила, если требуется вернуть
   общий доступ. Это небезопасно и должно выполняться только по явному решению.
5. Откатить commit с publisher/source pages и снова запустить
   `publish_it_wiki.py`, если требуется снять каталог оборудования.
