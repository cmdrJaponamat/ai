# Восстановление SSH-доступа по ключу на SPB-MX3

Дата: 2026-10-01

## Проблема

На `SPB-MX3` (`10.78.3.62`) доменная учётная запись
`AURORA-LOGISTIC\admin-al` принимала пароль, но не принимала локальный
Ed25519-ключ `/home/admin-al/.ssh/id_ed25519`.

## Причина и проверка

- Ключ в `C:\ProgramData\ssh\administrators_authorized_keys` совпадал с
  локальным ключом (SHA256 `j/XhMH0OphjBvsu1I8qPOP823fKezhs0W3UwTjF7pSA`).
- Файл и его ACL были корректны.
- `sshd_config` назначает этот файл только внутри
  `Match Group administrators`.
- Для данной доменной учётной записи, входящей в локальные Administrators
  через вложенную `Domain Admins`, это условие не применилось. Фактическим
  стандартным путём стал `C:\Users\admin-al\.ssh\authorized_keys`, которого
  не было.

## Изменение

Созданы:

- `C:\Users\admin-al\.ssh`;
- `C:\Users\admin-al\.ssh\authorized_keys` с уже применяемым Ed25519 public
  key.

У наследования ACL отключено. Полный доступ имеют только
`AURORA-LOGISTIC\admin-al` и `SYSTEM`. Конфигурация `sshd`, ключи других
пользователей и состояние службы не менялись.

## Проверка

Успешно выполнен key-only вход:

```text
ssh -l 'admin-al@aurora-logistics.local' -i ~/.ssh/id_ed25519 10.78.3.62
```

Сервер вернул `spb-mx3` и `aurora-logistic\admin-al`; запроса пароля не было.

## Откат

Если персональный ключ больше не требуется, удалить только
`C:\Users\admin-al\.ssh\authorized_keys`, затем пустой каталог `.ssh`.
Перезапуск `sshd` и перезагрузка не нужны.
