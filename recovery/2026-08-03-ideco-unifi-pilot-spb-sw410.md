# Ideco + UniFi pilot: подготовка L2 на SPB-SW-410

Дата: 2026-08-03, MSK

## Задача

Подготовить отдельный путь для тестового SSID через Ideco, не подключая новый кабель и не меняя существующие SSID, шлюз `AL-SPB-MILLION` или его uplink.

## Подтверждённая топология

- `SPB-SW-410` — `192.168.203.6`, MikroTik CRS328.
- Ideco уже подключён как управляющее устройство: `SPB-SW-410 ether13` ↔ `Ideco Leth1`, адрес Ideco `192.168.203.82/24`, VLAN 30.
- `SPB-SW-410 ether7` — работающая UniFi-точка `SPB410IT` (`192.168.203.212`).
- `SPB-SW-410 ether6` до изменения был в состоянии `no-link` и не имел назначенной роли.
- Uplink `SPB-SW-410 ether1` идёт к `AL-SPB-MILLION ether3`; VLAN 1460 в него не добавлялся.
- Для изолированного выхода пилота подготовлен отдельный транзит `VLAN 1461`: `SPB-SW-410 ether11` (access) ↔ Ideco и `SPB-SW-410 ether1` (tagged) ↔ `AL-SPB-MILLION ether3` (tagged).

## Выполненные изменения

На `SPB-SW-410`:

```routeros
/interface ethernet poe set ether6 poe-out=off
/interface ethernet set ether6 comment="Ideco TEST-LAN VLAN1460 tagged-only"
/interface bridge port set [find where interface=ether6] pvid=1 frame-types=admit-only-vlan-tagged ingress-filtering=yes
/interface bridge vlan add bridge=Bridge-LAN vlan-ids=1460 tagged=ether6,ether7 comment="Ideco WiFi pilot: SPB410IT only"
/interface ethernet set ether13 comment="Ideco MANAGEMENT 192.168.203.82"
```

После подготовки подключены оба кабеля Ideco. `SPB-SW-410 ether6` (VLAN 1460) и `ether11` (VLAN 1461) поднялись на 1 Гбит/с full-duplex. SSID на UniFi Controller пока не создавался.

На `SPB-SW-410` для транзита:

```routeros
/interface ethernet poe set ether11 poe-out=off
/interface ethernet set ether11 comment="Ideco TRANSIT VLAN1461 untagged"
/interface bridge port set [find where interface=ether11] pvid=1461 frame-types=admit-only-untagged-and-priority-tagged ingress-filtering=yes
/interface bridge vlan add bridge=Bridge-LAN vlan-ids=1461 tagged=ether1 untagged=ether11 comment="Ideco pilot transit to AL-SPB-MILLION"
```

На `AL-SPB-MILLION`:

```routeros
/interface vlan add name=vlan1461-ideco-transit interface=Bridge-LAN vlan-id=1461 comment="Ideco pilot transit"
/ip address add address=172.31.146.1/30 interface=vlan1461-ideco-transit comment="Ideco pilot transit gateway"
/interface bridge vlan add bridge=Bridge-LAN vlan-ids=1461 tagged=Bridge-LAN,ether3 comment="Ideco pilot transit to SW-410"
/ip firewall filter add chain=forward action=accept in-interface=vlan1461-ideco-transit out-interface-list=WAN comment="Ideco pilot transit to WAN" place-before=[find where comment="drop forward"]
```

На Ideco через штатный web API:

- LAN на MAC `1c:57:d8:18:de:00`, tagged `VLAN 1460`, адрес `10.76.146.1/24`;
- DHCP на `10.76.146.50–10.76.146.200`, DNS `10.78.4.253, 1.1.1.1`, lease 1 час;
- WAN на MAC `1c:57:d8:18:de:01`, адрес `172.31.146.2/30`, шлюз `172.31.146.1`;
- автоматический SNAT Ideco включён. Отдельное правило NAT не требуется.

Создана контрольная резервная копия Ideco после подготовки: `backup-20260803212307-Bez-nazvaniya-c4c5c30a-3d6a-4bb1-9bbe-98e0ff155051-ideco-utm-fstek-19-20-14.tbz`.

## Проверка

```routeros
/interface bridge vlan print detail where vlan-ids=1460
/interface ethernet monitor ether6 once
/interface ethernet poe print detail where name=ether6
/interface bridge port print detail where interface=ether6
```

Фактический результат: VLAN 1460 имеет только tagged-порты `ether6,ether7`; VLAN 1461 идёт tagged `ether1` / untagged `ether11`. Оба линка работают на 1 Гбит/с, PoE на коммутаторе отключено. Ideco сохраняет доступность по `Leth1` / `192.168.203.82`; Ideco и MikroTik отвечают друг другу по `172.31.146.2` / `172.31.146.1`, а выход Ideco через транзит до `1.1.1.1` подтверждён.

## Откат

```routeros
/interface bridge vlan remove [find where vlan-ids=1460]
/interface bridge port set [find where interface=ether6] frame-types=admit-all ingress-filtering=yes pvid=1
/interface ethernet poe set ether6 poe-out=auto-on
/interface ethernet set ether6 comment=""

/interface bridge vlan remove [find where vlan-ids=1461]
/interface bridge port set [find where interface=ether11] pvid=30 frame-types=admit-all ingress-filtering=yes
/interface ethernet poe set ether11 poe-out=auto-on
/interface ethernet set ether11 comment="SPB 410 big meeting room"
```

На `AL-SPB-MILLION`:

```routeros
/ip firewall filter remove [find where comment="Ideco pilot transit to WAN"]
/interface bridge vlan remove [find where vlan-ids=1461]
/ip address remove [find where address="172.31.146.1/30"]
/interface vlan remove [find where name="vlan1461-ideco-transit"]
```

Откат не влияет на `ether13` (управление Ideco), `ether7` (рабочая точка) или `ether1` (uplink MikroTik).

## Следующий шаг

Кабели подключены строго по MAC-адресам сетевых карт Ideco (не по внутреннему имени ОС):

1. `1c:57:d8:18:de:00` ↔ `SPB-SW-410 ether6` — VLAN 1460 tagged.
2. `1c:57:d8:18:de:01` ↔ `SPB-SW-410 ether11` — VLAN 1461 untagged.

Проверены линк, маршрут до `172.31.146.1`, DNS и интернет со стороны Ideco. Следующий шаг — создать и назначить SSID на `SPB410IT`, затем проверить DHCP и доступ одним тестовым клиентом.

## Перезапуск

Не требуется.
