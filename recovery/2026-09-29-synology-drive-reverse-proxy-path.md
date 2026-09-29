# SPB-NAS1: подготовка связности reverse proxy для Synology Drive

**Дата:** 2026-09-29  
**NAS:** `SPB-NAS1` / `spb-file-cloud`  
**Reverse proxy:** `10.78.3.1` (`nginx`)

## Цель

Подготовить минимальный внутренний transport path для будущего веб-доступа к
Synology Drive через `cloud.aurora-logistics.ru`. DSM не публикуется напрямую
в Internet.

## Изменение

На `AL-OBIT` включено заранее подготовленное правило RouterOS:

```text
comment: STORAGE-FILE staged: reverse proxy to Drive
chain: forward
action: accept
protocol: tcp
src-address: 10.78.3.1
dst-address-list: STORAGE-FILE (SPB-NAS1 = 10.78.7.10)
dst-port: 5001
```

Правило было расположено после финального `[DROP_ALL]`, поэтому не работало.
Оно перенесено непосредственно перед этим запретом. Других firewall/NAT-правил
не добавлялось и не изменялось.

## Проверка

С reverse proxy выполнено:

```bash
curl -k -I --connect-timeout 10 https://10.78.7.10:5001
```

Результат: `HTTP/2 200`; счетчик правила на RouterOS увеличился.

## Не выполнено / блокер

- Пакет Synology Drive, ввод NAS в AD, Team Folder `share`, политики ссылок
  и Nginx vhost ещё не настраивались.
- Сохраненная DSM учетная запись `ansible` на `10.78.0.250` отклоняет
  аутентификацию. Повторная проверка 2026-09-29: эталонный пароль
  automation-учетки MikroTik также отклонен по SSH. До восстановления
  административного входа не менять настройки DSM и не публиковать
  `cloud.aurora-logistics.ru`.

## Следующий безопасный порядок

1. Восстановить или подтвердить административный вход DSM для `ansible`.
2. Ввести NAS в `aurora-logistics.local`, проверить DNS/NTP/Kerberos.
3. Установить Synology Drive Server, включить Team Folder `share`.
4. Для пользователей Drive включить самостоятельные public links с
   обязательным паролем, сроком 3 дня и только download/view.
5. Настроить отдельный file-request destination для внешней загрузки.
6. Создать Nginx vhost и сертификат для `cloud.aurora-logistics.ru`, затем
   выполнить внутренний и внешний тесты. Открывать только TCP/443 до Nginx.

## Откат

На `AL-OBIT`:

```routeros
/ip firewall filter disable [find where comment="STORAGE-FILE staged: reverse proxy to Drive"]
```

Это немедленно закрывает transport path `10.78.3.1 → 10.78.7.10:5001` и не
затрагивает SMB, NFS, management NAS или другие опубликованные сервисы.

**Relogin/restart/reboot:** не требуется.
