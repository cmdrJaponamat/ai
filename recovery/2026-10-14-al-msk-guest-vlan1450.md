# AL-MSK: guest Wi-Fi VLAN 1450

## Задача

Перевести гостевой Wi-Fi Москвы на AL-MSK (RouterOS `MSK-office`) после вывода тестового Ideco, сохранив legacy guest VLAN 2 без изменений.

## Подтверждённое исходное состояние

- VLAN 1450 уже транспортируется tagged: `AL-MSK ether1` → `MSK-office-SW1 ether24` → AP-порты `ether4`–`ether8`.
- На AL-MSK отсутствуют L3-интерфейс, адрес, DHCP и firewall-правила VLAN 1450.
- В AL-MSK есть устаревший маршрут `10.77.45.0/24 via 172.17.254.6` и tagged membership `ether14`, оставшиеся от Ideco.
- Свободных ARP- и DHCP-записей в `10.77.45.0/24` нет.

## Выполненные изменения

- `vlan1450-guest` на `bridge-LAN`, VLAN ID 1450, шлюз `10.77.45.254/24`.
- DHCP `10.77.45.20–10.77.45.253`, DNS `77.88.8.8,77.88.8.2`.
- Разрешён только выход guest VLAN в WAN; вход к самому AL-MSK после DHCP блокируется.
- Устаревшие route и tag на `ether14` удаляются. Legacy VLAN 2 не затрагивается.

На `MSK-office` выполнено:

- сохранены `pre-guest-vlan1450-20261014.backup` и `.rsc` в локальном файловом хранилище RouterOS;
- bridge VLAN 1450 переименован в `Guest Wi-Fi VLAN 1450`, оставлен tagged только на `bridge-LAN,ether1`;
- созданы `vlan1450-guest`, `10.77.45.254/24`, DHCP pool/server `dhcp-vlan1450-guest` и DHCP network;
- добавлены input allow DHCP и последующий deny доступа guest к AL-MSK перед legacy catch-all;
- добавлено forward allow только `vlan1450-guest` → WAN перед `drop all other`;
- удалён только маршрут `10.77.45.0/24 via 172.17.254.6` с комментарием `Ideco MSK target return route`.

## Проверка

- VLAN interface имеет состояние `running`.
- AL-MSK показывает connected route `10.77.45.0/24` через `vlan1450-guest`.
- `ping 1.1.1.1 src-address=10.77.45.254 count=3`: 3/3, среднее 1.847 ms.
- На момент работ в DHCP/ARP guest-подсети не было клиентов; нужна проверка DORA после подключения устройства к guest SSID.

## Проверка клиентом после подключения

- Windows-клиент `DESKTOP-LF2D2G1` получил bound DHCP lease `10.77.45.253`.
- Счётчик правила `GUEST VLAN1450 Internet only` увеличился; final drop не затронул traffic guest-клиента.
- Conntrack подтвердил исходящие TCP/443-сессии с NAT на WAN и обратный трафик, а также DNS-ответы от `77.88.8.8` и `77.88.8.2`.
- Ранее отображавшийся у клиента статус «без доступа в Интернет» совпал с неполным DHCP-обменом (`offered`); после переподключения DORA завершён, доступ подтверждён.

## Откат

На AL-MSK удалить только объекты с именем/комментарием `vlan1450-guest`, `dhcp-vlan1450-guest` и `GUEST VLAN1450`; удалить IP `10.77.45.254/24`; вернуть tagged `ether14` в bridge VLAN 1450 и статический маршрут `10.77.45.0/24 via 172.17.254.6` только если Ideco снова станет шлюзом.

## Требование перезапуска

Не требуется. Клиентам guest SSID нужно переподключиться или обновить DHCP-lease.
