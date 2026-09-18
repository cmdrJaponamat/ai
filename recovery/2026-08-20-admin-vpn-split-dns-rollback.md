# Откат неудачной настройки split-DNS для admin-vpn

## Событие

20 августа 2026 была предпринята настройка маршрутного DNS для
`aurora-logistics.local` через Unbound `10.78.4.253` и `systemd-resolved`.
Во время применения `resolvectl` получил таймаут активации D-Bus службы
`org.freedesktop.resolve1`. Решение не было введено в эксплуатацию.

## Итоговое состояние

- `systemd-resolved` выключен и отключён;
- `/etc/resolv.conf` восстановлен в исходный вариант NetworkManager;
- `/etc/NetworkManager/conf.d/90-systemd-resolved.conf` удалён;
- helper OpenVPN удалён;
- `/home/admin-al/work/admin-vpn.ovpn` восстановлен из
  `admin-vpn.ovpn.bak-20260820-160951`;
- `tun0` и маршрут к `10.78.4.253` через VPN остались работоспособны.

## Важное ограничение

Не применять split-DNS через `systemd-resolved` на этом ПК без отдельной
диагностики причины таймаута и согласованного плана отката.
