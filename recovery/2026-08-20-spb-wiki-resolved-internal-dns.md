# spb-wiki: восстановление внутреннего DNS для PortalAL

Дата: 2026-08-20

## Симптом

PortalAL на `spb-wiki` (`10.78.3.149`) не мог разрешить
`spb-dc1-al.aurora-logistics.local`; контейнер и задания синхронизации
получали `getaddrinfo ENOTFOUND`. Перезапуск `systemd-resolved` в 10:10 MSK
восстановил разрешение имён.

## Исправление

В постоянной конфигурации интерфейса `ens18` одновременно были заданы
`10.78.3.50` и публичный `8.8.8.8`. Публичный сервер возвращает NXDOMAIN для
частной зоны `aurora-logistics.local`. Публичный resolver удалён: для линка
оставлен только доменный DNS `10.78.3.50`.

Изменённый файл: `/etc/systemd/network/10-static-ens18.network`.

Резервная копия: `/etc/systemd/network/10-static-ens18.network.bak-20260820-112701`.

Применение: `systemctl reload systemd-networkd`, `networkctl reconfigure ens18`,
`resolvectl flush-caches`.

## Проверка

```bash
resolvectl query spb-dc1-al.aurora-logistics.local
docker exec portal-al node -e "require('dns').lookup('spb-dc1-al.aurora-logistics.local',{all:true},console.log)"
```

Ожидаемый адрес: `10.78.3.50`.

## Откат

```bash
sudo cp -a /etc/systemd/network/10-static-ens18.network.bak-20260820-112701 /etc/systemd/network/10-static-ens18.network
sudo systemctl reload systemd-networkd
sudo networkctl reconfigure ens18
sudo resolvectl flush-caches
```
