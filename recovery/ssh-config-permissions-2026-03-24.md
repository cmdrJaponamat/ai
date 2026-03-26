# SSH Config Permissions Recovery

Дата: 2026-03-24
Область: system work, SSH client config, git push

## Problem Statement

- `git push` из `/home/japonamat/study/vkr` не проходит.
- OpenSSH завершает работу с ошибкой `Bad owner or permissions on /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf`.

## Findings

- `/etc/ssh` имеет владельца и группу `nobody:nobody`.
- `/etc/ssh/ssh_config.d` имеет владельца и группу `nobody:nobody`.
- `/etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf` является симлинком на `/usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf`.
- Целевой файл `/usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf` тоже принадлежит `nobody:nobody`.
- Права целевого файла: `644`.
- Для симлинка выводился режим `777`, но критичная проблема здесь в неправильном owner/group у директорий и целевого файла.

## Exact Changes Made

- Изменений в системные пути пока не внесено.
- Создан recovery trail с диагностикой и планом исправления.

## Verification Status

- Проверка причин сбоя выполнена командами `stat`, `ls`, `readlink`, `sed`.
- Причина ошибки подтверждена.
- Исправление еще не применено, повторная проверка `git push` пока ожидает root-правки.

## Rollback

- Откат не требуется, так как системные файлы пока не изменялись.
- После применения исправления штатный rollback не нужен; при ошибочном применении нужно вручную вернуть корректные владельца и права для `/etc/ssh` и `/usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf`.

## Relogin Or Reboot

- Не нужен.

## Manual Fix

```bash
sudo chown root:root /etc/ssh /etc/ssh/ssh_config.d /usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf
sudo chmod 755 /etc/ssh /etc/ssh/ssh_config.d
sudo chmod 644 /usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf
```

Если нужна явная перестановка симлинка:

```bash
sudo ln -sfn ../../../usr/lib/systemd/ssh_config.d/20-systemd-ssh-proxy.conf /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf
```

## Post-Fix Check

```bash
ssh -G git@github-auto >/dev/null
git -C /home/japonamat/study/vkr push origin main
```
