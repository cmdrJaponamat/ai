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

## Выполненные изменения

На `SPB-SW-410`:

```routeros
/interface ethernet poe set ether6 poe-out=off
/interface ethernet set ether6 comment="Ideco TEST-LAN VLAN1460 tagged-only"
/interface bridge port set [find where interface=ether6] pvid=1 frame-types=admit-only-vlan-tagged ingress-filtering=yes
/interface bridge vlan add bridge=Bridge-LAN vlan-ids=1460 tagged=ether6,ether7 comment="Ideco WiFi pilot: SPB410IT only"
/interface ethernet set ether13 comment="Ideco MANAGEMENT 192.168.203.82"
```

На момент записи `ether6` по-прежнему без линка. Кабель между `Ideco eth1` и `SPB-SW-410 ether6` не подключался. SSID на UniFi Controller не создавался.

## Проверка

```routeros
/interface bridge vlan print detail where vlan-ids=1460
/interface ethernet monitor ether6 once
/interface ethernet poe print detail where name=ether6
/interface bridge port print detail where interface=ether6
```

Ожидаемый результат: VLAN 1460 имеет только tagged-порты `ether6,ether7`; `ether6` inactive/no-link и `poe-out=off`.

## Откат

```routeros
/interface bridge vlan remove [find where vlan-ids=1460]
/interface bridge port set [find where interface=ether6] frame-types=admit-all ingress-filtering=yes pvid=1
/interface ethernet poe set ether6 poe-out=auto-on
/interface ethernet set ether6 comment=""
```

Откат не влияет на `ether13` (управление Ideco), `ether7` (рабочая точка) или `ether1` (uplink MikroTik).

## Следующий шаг

Через штатный веб-интерфейс Ideco создать на физическом `eth1` tagged-интерфейс VLAN 1460, назначить согласованную тестовую подсеть, DHCP, исходящий NAT и наблюдающую политику контроля приложений. Затем до физического подключения повторно проверить `ether6=no-link` и `poe-out=off`.

## Перезапуск

Не требуется.
