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
/ip route add dst-address=10.76.146.0/24 gateway=172.31.146.2 comment="Ideco WiFi pilot return route"
```

На Ideco через штатный web API:

- LAN на MAC `1c:57:d8:18:de:00`, tagged `VLAN 1460`, адрес `10.76.146.1/24`;
- DHCP на `10.76.146.50–10.76.146.200`, DNS `10.78.4.253, 1.1.1.1`, lease 1 час;
- WAN на MAC `1c:57:d8:18:de:01`, адрес `172.31.146.2/30`, шлюз `172.31.146.1`;
- на первом тесте трафик маскируется существующим общим src-NAT MikroTik при выходе в WAN; добавленный обратный маршрут возвращает ответы через Ideco. Автоматический SNAT Ideco включён, но для этой схемы не требуется.

Создана контрольная резервная копия Ideco после подготовки: `backup-20260803212307-Bez-nazvaniya-c4c5c30a-3d6a-4bb1-9bbe-98e0ff155051-ideco-utm-fstek-19-20-14.tbz`.

## Проверка

```routeros
/interface bridge vlan print detail where vlan-ids=1460
/interface ethernet monitor ether6 once
/interface ethernet poe print detail where name=ether6
/interface bridge port print detail where interface=ether6
```

Фактический результат: VLAN 1460 имеет только tagged-порты `ether6,ether7`; VLAN 1461 идёт tagged `ether1` / untagged `ether11`. Оба линка работают на 1 Гбит/с, PoE на коммутаторе отключено. Ideco сохраняет доступность по `Leth1` / `192.168.203.82`; Ideco и MikroTik отвечают друг другу по `172.31.146.2` / `172.31.146.1`, а выход Ideco через транзит до `1.1.1.1` подтверждён.

## Первый клиентский тест

- телефон `realme-10` получил аренду `10.76.146.173` (MAC `d2:7a:44:ce:58:9d`);
- шлюз Ideco отвечает, MikroTik также достигает клиента через маршрут возврата;
- DNS к `1.1.1.1` получает ответы;
- подтверждены полноценные TCP-сессии телефона по HTTP/HTTPS и UDP-сессия прикладного сервиса;
- доступ к рабочим SSID и VLAN 30 не менялся.

## Контроль приложений: режим наблюдения

На Ideco создан отдельный профиль DPI `Wi-Fi pilot — observe only` (ID `01KZ5SDB5K75VW18XE8VA9HK1M`). В нём все 439 доступных протоколов имеют действие `allow`; профиль не содержит блокировок.

Созданы:

- alias `subnet.id.1`: `Wi-Fi pilot VLAN 1460` = `10.76.146.0/24`;
- одно firewall-правило forward ID `1`: только входящий `interface.id.2` (VLAN 1460), источник `subnet.id.1`, действие `accept`, DPI включён, IPS выключен, выход — любой.

Глобальный application control и службы `app-control` / `app-control-nfq` активны. TLS inspection не включался.

Проверка 2026-08-04: после соединений, принудительно направленных через Wi-Fi ноутбука `10.76.146.135`, монитор Ideco классифицировал `OpenVPN`, `TLS`, `DTLS`, `QUIC`, `Google`, `GoogleDocs`, `Cloudflare`, `HTTP` и `SSH`. У телефона `10.76.146.173` распознаны `QUIC` и `TLS`.

Важно: у ноутбука запущен FlClashX, поэтому блокирование `OpenVPN`, `DTLS` или части TLS/QUIC в текущем состоянии может оборвать рабочее соединение. До отдельного согласования выполняется только наблюдение.

## Интеграция с Active Directory

Ideco введён в домен `AURORA-LOGISTICS.LOCAL` как компьютер `IDECO-SPB-PILOT$` (идентификатор интеграции `60264205-8484-4462-afa8-401fd82008f4`). Для домена зафиксированы:

- DNS AD: `10.78.3.50`;
- KDC/LDAP: `spb-dc1-al.aurora-logistics.local` (его адрес `10.78.3.50`);
- импорт групп: без LDAP-фильтра, штатный импорт всех групп безопасности.

Причина фиксации KDC по FQDN: Kerberos не имеет service principal для `ldap/10.78.3.50`; он есть для `ldap/spb-dc1-al.aurora-logistics.local`. Проверены получение machine ticket из `/run/ideco-ad-backend/aurora-logistics.local.keytab` и GSSAPI LDAP к FQDN DC. Ideco импортировал 162 групп безопасности; это не создаёт разрешающих или запрещающих правил и не меняет сессии пользователей.

Для следующего этапа — авторизации по журналам AD и политик на группы — на DC необходимо:

1. добавить компьютер `IDECO-SPB-PILOT$` в группу `Event Log Readers`;
2. включить Windows Firewall group `Remote Event Log Management`, ограничив источник `192.168.203.82`;
3. после этого включить в Ideco авторизацию через журналы AD и проверить одну доменную учётную запись на пилотной подсети.

До выполнения этих трёх пунктов служба сбора AD-журналов ожидаемо не активна. Откат интеграции: удалить домен через Ideco Users → Active Directory/Samba DC, затем удалить компьютер `IDECO-SPB-PILOT$` в AD.

Пункты выполнены 2026-08-04: компьютер добавлен в локализованную встроенную AD-группу `Читатели журнала событий` (well-known SID `S-1-5-32-573`); на `spb-dc1-al` включена группа правил Windows Firewall `Remote Event Log Management` с источником только `192.168.203.82`. В Ideco включена настройка `authorization_by_logs`. Служба `ideco-ad-log-collector@aurora-logistics.local` активна и уже собрала четыре действующих соответствия IP ↔ доменная учётная запись, поэтому связка AD и удалённого журнала подтверждена.

Это не является блокировкой: правило пилотной сети по-прежнему разрешает трафик, а DPI-профиль только наблюдает. Чтобы проверить пользовательскую политику, нужен доменный Windows-ноутбук в `Aurora-Security-Pilot`: после входа пользователя в Windows и первой попытки доступа через Ideco в его списке сессий должен появиться IP `10.76.146.x` и доменная учётная запись.

Так как пилотный транзит изначально разрешал только WAN, на `AL-SPB-MILLION` добавлены два узких исключения перед `drop forward`:

```routeros
/ip firewall filter add chain=forward action=accept in-interface=vlan1461-ideco-transit dst-address=10.78.3.50 protocol=udp dst-port=53,88 comment="Ideco pilot AD DNS-Kerberos UDP" place-before=[find where comment="drop forward"]
/ip firewall filter add chain=forward action=accept in-interface=vlan1461-ideco-transit dst-address=10.78.3.50 protocol=tcp dst-port=53,88 comment="Ideco pilot AD DNS-Kerberos TCP" place-before=[find where comment="drop forward"]
```

Они нужны только для DNS и Kerberos к одному DC; пилот не получает маршрут в другие подсети. Откат:

```routeros
/ip firewall filter remove [find where comment="Ideco pilot AD DNS-Kerberos UDP"]
/ip firewall filter remove [find where comment="Ideco pilot AD DNS-Kerberos TCP"]
```

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
/ip route remove [find where comment="Ideco WiFi pilot return route"]
/interface bridge vlan remove [find where vlan-ids=1461]
/ip address remove [find where address="172.31.146.1/30"]
/interface vlan remove [find where name="vlan1461-ideco-transit"]
```

На Ideco сначала удалить правило forward ID `1`, затем alias `subnet.id.1` и профиль DPI `01KZ5SDB5K75VW18XE8VA9HK1M` через GUI или соответствующие API. Удаление этого профиля возвращает VLAN 1460 к базовому пропуску трафика без прикладной классификации.

Откат не влияет на `ether13` (управление Ideco), `ether7` (рабочая точка) или `ether1` (uplink MikroTik).

## Следующий шаг

Кабели подключены строго по MAC-адресам сетевых карт Ideco (не по внутреннему имени ОС):

1. `1c:57:d8:18:de:00` ↔ `SPB-SW-410 ether6` — VLAN 1460 tagged.
2. `1c:57:d8:18:de:01` ↔ `SPB-SW-410 ether11` — VLAN 1461 untagged.

Проверены линк, маршрут до `172.31.146.1`, DNS и интернет со стороны Ideco. SSID создан, первый тестовый клиент прошёл DHCP, DNS и HTTP/HTTPS, а наблюдающая классификация приложений включена. Следующий шаг — согласовать один безопасный объект для тестовой блокировки, ограниченный только пилотной подсетью.

## Перезапуск

Не требуется.

## Доступ к shared_srvs для пилотного VLAN

### Причина

Для доменной авторизации клиенту недостаточно одного `spb-dc1-al`: DNS SRV может
вернуть другой контроллер домена (`dc2` `10.10.20.50`). Вместо привязки к одному
DC пилотной сети дан контролируемый доступ ко всему уже существующему списку
`shared_srvs` на `AL-SPB-MILLION`.

### Изменения 2026-08-04

На Ideco создано активное правило policy routing `Ideco pilot: shared_srvs via
AL-SPB-MILLION`:

- источник: `10.76.146.0/24` (`subnet.id.1`);
- назначение: статический снимок 16 адресов `shared_srvs`
  (`ip_address_list.id.1`);
- шлюз: транзитный интерфейс Ideco `Eeth3` (`172.31.146.2 → 172.31.146.1`).

Список применён также как разрешённый ресурс до авторизации пользователя. Это
не даёт пилотному VLAN общий доступ в корпоративную сеть или интернет: до
авторизации доступны только адреса из списка; после авторизации остальная
политика Ideco остаётся отдельной.

На `AL-SPB-MILLION` добавлено правило перед `drop forward`:

```routeros
/ip firewall filter add chain=forward action=accept \
    in-interface=vlan1461-ideco-transit dst-address-list=shared_srvs \
    comment="Ideco pilot to shared_srvs" \
    place-before=[find where comment="drop forward"]
```

На `AL-OBIT` создан зеркальный список `IdecoPilotSharedSrvs` из тех же 16
адресов и правило перед финальным `[DROP_ALL]`:

```routeros
/ip firewall filter add chain=forward action=accept \
    src-address=10.76.146.0/24 dst-address-list=IdecoPilotSharedSrvs \
    comment="Ideco pilot to shared_srvs" \
    place-before=[find where log-prefix="[DROP_ALL]"]
```

Отдельные маршруты не добавлялись: на `AL-SPB-MILLION` уже активны
`10.10.0.0/16 → WG-AL-MMK` и `10.78.0.0/16 → WG-SPB-DC`.

### Проверка

Оба policy-route на Ideco активны. Проверка ядра Ideco с меткой правила
подтвердила путь `10.10.20.50`, `10.10.40.149`, `10.78.22.3` через
`172.31.146.1/Eeth3`. Окончательная клиентская проверка выполняется с
ноутбука в SSID VLAN 1460:

```powershell
Test-NetConnection 10.10.20.50 -Port 88
nltest /dsgetdc:aurora-logistics.local /force
klist purge
klist get krbtgt
```

### Откат

```routeros
# AL-SPB-MILLION
/ip firewall filter remove [find where comment="Ideco pilot to shared_srvs"]

# AL-OBIT
/ip firewall filter remove [find where comment="Ideco pilot to shared_srvs"]
/ip firewall address-list remove [find where list="IdecoPilotSharedSrvs"]
```

На Ideco удалить policy-rule с идентификатором `2`, alias `ip_address_list.id.1`
и ресурс pre-auth, ссылающийся на него. Потребуется также удалить или изменить
связанные записи только после того, как правило не используется. Перезапуск не
нужен.
