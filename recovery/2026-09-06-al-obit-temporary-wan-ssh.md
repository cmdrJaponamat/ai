# Временный WAN SSH к AL-OBIT

Дата: 2026-09-06. Назначение: страховочный доступ на время перехода uplink с
cross-switch LACP на active-backup.

## Изменение

- На `AL-OBIT` создана динамическая address-list запись
  `TEMP-WAN-ADMIN = 87.248.239.0/24` с timeout 4 часа.
- Перед штатным правилом `drop ssh !spb lan` добавлено правило
  `TEMP WAN SSH active-backup window`: разрешён только TCP/22, только с
  `TEMP-WAN-ADMIN`, только через `in-interface-list=WAN`.
- WinBox, WebFig, API и другие порты наружу не открывались.
- Созданы файлы на роутере:
  - `pre-active-backup-wan-recovery-20260906.backup`;
  - `pre-active-backup-wan-recovery-20260906.rsc` (`hide-sensitive`).

## Проверка

С ноутбука через мобильную сеть выполнен SSH-вход с ключом на все публичные
адреса AL-OBIT:

- `85.114.6.214` (ether16/ISP1);
- `79.134.216.142` (ether15/ISP2);
- `178.16.150.38` (ether15/ISP3).

Во всех случаях прочитан identity `AL-OBIT`. Счётчик временного правила после
проверки: 5 пакетов / 300 байт.

## Ограничение

Мобильный адрес динамический. Разрешена текущая операторская `/24`, что
переживёт смену адреса внутри подсети, но не переход в другую `/24`. Перед
опасным этапом повторно проверить внешний адрес и WAN SSH. Address-list запись
удалится сама через 4 часа; статическое firewall-правило после окна нужно
удалить вручную, иначе оно останется бездействующим с пустым списком.

## Откат/закрытие окна

```routeros
/ip firewall filter remove [find where comment="TEMP WAN SSH active-backup window"]
/ip firewall address-list remove [find where list="TEMP-WAN-ADMIN"]
```

После удаления подтвердить отсутствие обоих объектов. Восстановление полного
backup не требуется и затронуло бы несвязанные настройки.

Relogin/reboot не требуется.
