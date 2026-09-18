# Yandex Cloud CLI: профиль сервисного аккаунта

## problem_statement

Для работы с ресурсами Yandex Cloud с этого ПК требовался отдельный,
неинтерактивный профиль без использования личной учётной записи в командах.

## exact_changes_made

- Официальный `yc` CLI 1.24.0 установлен в `/home/admin-al/yandex-cloud`.
- Инсталлятор добавил PATH и bash completion в `/home/admin-al/.bashrc`.
- Создан активный профиль `admin-al-service`.
- Профиль использует JSON-ключ из
  `/home/admin-al/assistant/.secrets/yandex-cloud/authorized_key.json`;
  права файла приведены к `600`.
- Профилю заданы cloud `b1ggsfe0harjisab5u98` (`aurora-logistics`) и folder
  `b1gdkj3s68vnth9foj8s` (`default`).

## verification_status

- `yc resource-manager folder get --id b1gdkj3s68vnth9foj8s` выполнена успешно.
- Read-only список VM показал `matix-service1`, `etl-service1`, `matix-db1` в
  состоянии `RUNNING`.
- Read-only список VPC показал сеть `default`.
- Запрос cloud-level объекта вернул `PermissionDenied`, что ожидаемо: права
  `viewer` назначены на каталог, а не на облако.

## rollback_strategy_or_note

```bash
/home/admin-al/yandex-cloud/bin/yc config profile delete admin-al-service
rm -rf /home/admin-al/yandex-cloud
```

Затем вручную удалить добавленные инсталлятором строки из `~/.bashrc` и
отозвать/удалить авторизованный ключ в консоли Yandex Cloud. JSON-ключ не
выводить и не передавать через чат.

## relogin_restart_or_reboot_requirement

Нужен только новый shell или `source ~/.bashrc`; перезагрузка не требуется.
