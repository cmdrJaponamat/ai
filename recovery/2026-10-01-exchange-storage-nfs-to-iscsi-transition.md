# Переход хранилища EXCH-3 с NFS на iSCSI

Дата: 2026-10-01

## Цель

Заменить NFS-backed хранилище, подготовленное для будущего третьего участника
Exchange DAG (`EXCH-3`), на block storage через Synology iSCSI.

## Причина

Microsoft не поддерживает хранение данных Exchange на NAS, представленном
гостевой ВМ через гипервизор. `cache=none` снижает риск write-back cache, но
не меняет тип хранилища. Для Exchange DB/log требуется block-level storage.

## Подтверждённое исходное состояние

- Proxmox storage `synology-exchange-dag` указывал на
  `10.78.5.10:/volume2/pve-exchange-dag` с NFSv4.1.
- На нём отсутствовали VM-диски: `pvesm list synology-exchange-dag` был пуст.
- В конфигурациях VM не найдено ссылок на этот storage.
- Выделенный пул Synology `/volume2` — RAID10 из `sdi`-`sdl`; он сохранён.

## Выполнено

- На PVE1 сохранён `/etc/pve/storage.cfg` как
  `/root/storage.cfg.pre-remove-synology-exchange-dag-20261001`.
- Удалена только пустая запись Proxmox `synology-exchange-dag`.
- RAID10 `/volume2`, NFS export и остальные storage не удалялись и не
  изменялись.

## Проверка

- После удаления `synology-exchange-dag` отсутствует в `/etc/pve/storage.cfg`.
- `pvesm status` подтверждает active-состояние всех оставшихся storage.
- PVE1/PVE2 не содержат конфигурационных ссылок на удалённый storage.

## Следующий этап

На SPB-NAS1 через DSM SAN Manager:

1. подтвердить доступность SAN Manager для конкретной модели;
2. создать отдельный iSCSI target и thick-provisioned LUN на `/volume2`;
3. ограничить target IQN PVE1/PVE2 и включить CHAP;
4. подключить LUN к PVE как block storage, провести flush/latency test;
5. для виртуальных дисков EXCH-3 использовать raw, `cache=none`,
   `virtio-scsi-single` и `iothread=1`.

DSM administrative access не был доступен в этой сессии, поэтому target/LUN не
создавались и аутентификация не обходилась.

## Откат

Пока iSCSI LUN не создан, восстановить NFS storage можно из сохранённого
`storage.cfg` PVE1. Не удалять `/volume2` или RAID10: он предназначен для
будущего iSCSI LUN.

## Reboot/relogin

Не требуется.
