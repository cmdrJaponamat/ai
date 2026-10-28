# Восстановление доступа Veeam к PBS — 2026-10-28

## Проблема и причина

`Backup Configuration Job` Veeam не мог перенести архив в `storage-on-pbs`.
Veeam использовал устаревший адрес PBS `10.78.3.178`. Фактический адрес
работающей PBS VM100 на PVE2 — `10.78.2.178/24`. Кроме того, Veeam находится
в VLAN1202 (`10.78.20.99`), а AL-OBIT блокировал трафик к PBS финальным
`DROP_ALL`.

## Изменение

- У существующего Veeam Linux-host object изменено имя `10.78.3.178` на
  `10.78.2.178` методом `SetName()`/`Update()`; GUID
  `60398476-5045-42e6-9553-adbd087d954b` и связанные backup chains сохранены.
- На AL-OBIT перед `DROP_ALL` добавлено единственное правило
  `Veeam to PBS repository before DROP_ALL`: TCP от `10.78.20.99` к
  `10.78.2.178` на порты 22, 6160, 6162 и 2500-3300. Это SSH, Veeam
  deployment/transport и временный Veeam data mover (фактически TCP/2501).

## Проверка

- PBS: SSH, Proxmox Backup Proxy и `/mnt/pbs-backups` активны; свободно около
  42 TiB.
- С AL-VEEAM доступны TCP 22, 6160, 6162 и 2501 на PBS.
- `storage-on-pbs`: host `10.78.2.178`, `IsUnavailable=False`.
- Ручной Configuration Backup от 28.10 10:26 MSK перенёс 1.5 MB в
  `storage-on-pbs`. Статус `Warning` вызван только отключённым encryption:
  credentials и server certificate не включены в конфигурационный архив.

## Откат

Удалить на AL-OBIT только правило с комментарием
`Veeam to PBS repository before DROP_ALL`. Старый адрес возвращать нельзя:
PBS VM100 фактически работает на `10.78.2.178`. Перезапуски не требуются.
