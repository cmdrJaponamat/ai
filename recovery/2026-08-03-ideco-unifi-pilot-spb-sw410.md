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

## Временная сетевая авторизация пилота

### Почему интернет пропадал

Отключение `Allow Internet Access to All` (аварийного «Полного доступа») не
является только отключением NAT. Оно снимает глобальное правило ACCEPT для
неавторизованного трафика. Поэтому клиент VLAN 1460 мог достичь лишь ресурсов,
явно перечисленных в `noauth_resources`, а интернет блокировался до появления
авторизованной сессии Ideco.

### Изменение 2026-08-04

Создана локальная техническая учётная запись Ideco `pilot_network_access`
(ID `3`, пароль случайный и не используется интерактивно) и штатное правило
сетевой авторизации:

```text
ID:       9e7ddcba-0581-4fd8-9a59-979377cf2625
Подсеть:  10.76.146.0/24
Статус:   enabled
Учётка:   pilot_network_access (ID 3)
```

Такое правило создаёт постоянную авторизованную сессию только для пилотной
подсети. Это временно отменяет требование интерактивной/AD-авторизации именно
для клиентов SSID VLAN 1460, но не включает `Allow Internet Access to All`, не
меняет `automatic_snat_enabled=false` и не выдаёт доступ к иным внутренним
адресам, кроме `shared_srvs` из предыдущего раздела. Сбор AD security logs и
IP ↔ пользователь продолжает работать для последующей проверки.

### Проверка

- `emergency_internet_access.enabled=false`;
- `ideco-auth-backend` active;
- правило сетевой авторизации отображается через `GET /auth/net_rules`.

С клиентского ноутбука нужно подтвердить обычный интернет и затем:

```powershell
Test-NetConnection 10.10.20.50 -Port 88
nltest /dsgetdc:aurora-logistics.local /force
klist purge
klist get krbtgt
```

### Откат

Сначала включить `Allow Internet Access to All` только если требуется сохранить
связь во время отката, затем удалить правило через `DELETE
/auth/net_rules/9e7ddcba-0581-4fd8-9a59-979377cf2625` и техническую учётную
запись через `DELETE /user_backend/users/3`. После перехода на подтверждённую
AD-авторизацию правило также должно быть удалено. Перезапуск не требуется.

## Результат проверки AD с AL-MMK-RE1

Проверка с `AL-MMK-RE1` (`10.76.146.147`) 2026-08-04 подтвердила штатную
работу доменной инфраструктуры через пилот:

- DNS `10.78.4.253` возвращает SRV-записи и для `spb-dc1-al`, и для `dc2`;
- TCP/88 до `spb-dc1-al` (`10.78.3.50`) доступен;
- `nltest /dsgetdc:aurora-logistics.local /force` успешно выбрал
  `spb-dc1-al`;
- `klist get krbtgt` успешно получил TGT для `a.kuznetsov`;
- Ideco в `/ad/auths_by_log/v2` зафиксировал соответствие
  `10.76.146.147 → a.kuznetsov@aurora-logistics.local`.

Следовательно, AD log authorization на Ideco технически работоспособна.

## Переход пилота на авторизацию по AD

### Изменение 2026-08-04

Для управления составом теста в AD создана security group `Net-Ideco-Pilot`
(`45eb1c1e-0dee-4068-8758-0a9bfaa778a7`). Она синхронизирована в одноимённую
группу Ideco `group.id.4` настройкой синхронизации
`49f2af86-f949-44e4-a4b8-06bb4059599e`. В Ideco импортированы только два
участника группы: `admin-al` и `a.kuznetsov`; весь домен не импортируется.

После получения нового трафика от `AL-MMK-RE1` Ideco создал авторизованную
сессию:

```text
subnet:      10.76.146.147/32
auth_module: log
login:       a.kuznetsov
group:       Net-Ideco-Pilot
domain:      aurora-logistics.local
```

Проверено также присутствие IP в `authorized_users`. Поэтому временное
правило сетевой авторизации VLAN 1460 и локальная учётная запись
`pilot_network_access` удалены, а не просто выключены. Сейчас выход из пилота
в интернет требует действующей сессии, полученной по журналам AD; глобальный
`Allow Internet Access to All` и автоматический SNAT по-прежнему выключены.

### Проверка для следующего пользователя

1. Добавить пользователя в AD-группу `Net-Ideco-Pilot`.
2. Подключить его доменный компьютер к SSID VLAN 1460.
3. Выполнить вход в Windows или обновить Kerberos-билет и создать новое внешнее
   соединение.
4. Убедиться на Ideco, что в `/auth/sessions/v3` появилась сессия с
   `auth_module=log`, правильным логином и IP `/32`.

Если сессия не создаётся, вернуть доступ нельзя включением общего аварийного
режима по умолчанию: сначала проверить запись IP → login в
`/ad/auths_by_log/v2`, импорт пользователя через AD-group sync и доступность
контроллера домена. Для экстренного восстановления можно временно включить
`Allow Internet Access to All`, но он включает глобальный пропуск и NAT.

### Отрицательная проверка

Подключённый второй ноутбук `10.76.146.199`
(`50:2e:91:2a:db:94`) не входит в `Net-Ideco-Pilot`. Ideco получил от него
запрос авторизации, но не имеет для адреса записи в `/ad/auths_by_log/v2` и
не добавил IP в `authorized_users`. Старые состояния conntrack, созданные до
перехода на AD, были удалены только для этого IP; после очистки активных
внешних соединений нет. Это подтверждает ожидаемое правило: подключение к
SSID само по себе доступа в интернет не даёт.

### Откат

Для временного обхода AD создать отдельную локальную техническую учётную
запись и сетевое правило `/auth/net_rules` строго на `10.76.146.0/24`; после
проверки удалить их. Не включать постоянный `Allow Internet Access to All`.

### Открытое ограничение dc2

`Test-NetConnection 10.10.20.50 -Port 88` с пилотного клиента пока не
проходит. На `AL-SPB-MILLION` правило `Ideco pilot to shared_srvs` получает
пакеты, а трассировка самого маршрутизатора до `dc2` успешно идёт через
`WG-AL-MMK` (`10.10.4.1 → 10.10.20.50`, около 20 мс). Вероятная причина — на
удалённой стороне peer WireGuard не содержит обратную сеть `10.76.146.0/24` в
`allowed-address` или нет обратного маршрута. Для исправления нужен
read/write-доступ к `AL-MMK`; на нём следует добавить только
`10.76.146.0/24` к peer, ведущему к `AL-SPB-MILLION`, и проверить обратный
маршрут. Это не блокирует текущую проверку AD: доменный контроллер
`spb-dc1-al` доступен и выдаёт Kerberos-билеты.

## Веб-аутентификация для недоменных устройств

### Назначение

Пользовательское устройство не обязано быть введено в AD. Для телефонов и
недоменных ноутбуков в пилотном SSID применяется та же доменная учётная
запись, но вместо сопоставления по журналам Windows пользователь вводит
`login` и пароль в captive portal Ideco.

Это не отдельный VLAN и не отдельный SSID: текущая граница уже обеспечена
VLAN 1460 и единственной пилотной точкой UniFi. Доменные Windows-клиенты
сохраняют действующий путь `auth_module=log`; веб-вход применяется, когда
клиент сам открывает страницу авторизации.

### Изменение 2026-08-04

На Ideco включён штатный сервис web-authd:

```json
{
  "enabled": true,
  "auth_type": "web",
  "self_domain_name": null
}
```

Настройка применена через локальный защищённый control endpoint
`http://127.0.0.1:11001/control` с действующей административной сессией.
Сервисы `ideco-web-authd`, `ideco-proxy-backend` и `squid` после изменения
остаются `active`.

Поскольку для пилота пока не выделено DNS-имя и доверенный сертификат,
первая проверка должна начинаться с HTTP, например `http://neverssl.com`.
При первом переходе на HTTPS браузер или телефон может показать
предупреждение о сертификате Ideco. Публичный DNS/Let's Encrypt для этой
внутренней схемы не требуются.

### Проверка

1. Подключить телефон или недоменный ноутбук к `Aurora-Security-Pilot`.
2. Открыть `http://neverssl.com`.
3. В форме Ideco ввести учётную запись AD, входящую в `Net-Ideco-Pilot`, и
   пароль этой учётной записи.
4. Проверить на Ideco, что создана сессия `auth_module=web` с IP клиента
   `/32`, правильным логином и группой `Net-Ideco-Pilot`.
5. Открыть HTTPS-сайт и убедиться в наличии выхода в интернет.

### Откат

Вернуть прежнее состояние одним запросом в локальной консоли Ideco:

```bash
curl -sS -X PUT -H 'Content-Type: application/json' \
  --data '{"enabled":false,"auth_type":"web","self_domain_name":null}' \
  http://127.0.0.1:11001/control
```

Либо в GUI Ideco: **Пользователи → Авторизация → Веб-аутентификация** снять
флаг включения. Вход по журналам AD и текущие правила доступа при этом не
изменяются. Перезапуск не требуется.

### Особенность первой проверки

Телефон `realme-10` (`10.76.146.173`, MAC `d2:7a:44:ce:58:9d`) был первым
клиентом пилота до включения обязательной авторизации. Поэтому его старые
conntrack-записи ещё позволяли продолжать созданные ранее соединения при
пустом `authorized_users`. 2026-08-04 удалены только состояния с источником
или назначением `10.76.146.173` (шесть записей); постоянные правила,
авторизация, DHCP и состояния остальных клиентов не изменялись. После этого
телефон должен создать новую web-сессию через форму Ideco, а не получить
доступ по старому соединению.

### Исправление пути выхода 2026-08-04

При проверке телефона выяснилось, что web-authd был включён корректно, но
сам трафик VLAN 1460 выбирал DHCP-шлюз управлящего интерфейса Ideco `Leth1`
(`192.168.203.1`). Этот интерфейс имеет тип LAN, поэтому штатное правило
Ideco «неавторизованному клиенту запрещён выход в E*» на него не
распространялось. В результате нельзя было считать captive portal
обязательным: в частности, UDP-трафик обходил HTTP/HTTPS-перехват.

`Leth1` переведён в статический режим с тем же адресом управления:

```text
Leth1: 192.168.203.82/24, gateway: none, DHCP: disabled
Eeth3: 172.31.146.2/30, gateway: 172.31.146.1, type: WAN
```

После изменения в таблицах маршрутизации Ideco не осталось дефолта через
`192.168.203.1`; дефолт WAN идёт через `Eeth3 → 172.31.146.1`.
Управление по `192.168.203.82` сохранено. Это не меняет рабочие SSID,
VLAN, UniFi или маршрутизацию пользователей: затронут только маршрут
самого пилотного шлюза.

Перед повторной проверкой телефона были удалены только его conntrack-сессии
`10.76.146.173`. Ожидаемое поведение: до успешного веб-входа устройство не
получает внешний трафик; после входа по учётной записи из
`Net-Ideco-Pilot` в Ideco появляется `auth_module=web` и доступ открывается.

Если требуется откат, в **Сеть → Интерфейсы** на записи «Локальный
интерфейс» вернуть DHCP и убрать статический адрес. Это вернёт прежний
обходной маршрут, поэтому применять откат только при явной необходимости
восстановить старую тестовую схему.

## Подготовка S2S Ideco Санкт-Петербург ↔ Москва

### Цель и границы пилота

Пилотный site-to-site строится между Ideco СПБ `192.168.203.82` и Ideco
Москва `10.77.0.253`. Это не замена существующих WireGuard/OpenVPN-каналов и
не изменение маршрутов пользователей. В туннель включаются только:

```text
СПБ pilot Wi-Fi: 10.76.146.0/24
Москва LAN:      10.77.0.0/24
VTI probe:       10.254.60.1/30 (СПБ) ↔ 10.254.60.2/30 (Москва)
```

Проверено до создания: `10.254.60.0/30` не встречается в доступном реестре
сетевых конфигураций. Московский Ideco имеет WAN `172.17.254.6/29` и LAN
`10.77.0.253/24`, IPsec на нём пока выключен. СПБ Ideco имеет WAN
`172.31.146.2/30` за публичным адресом AL-SPB-MILLION `31.187.97.119`.

### Транспорт

Инициатором будет московский Ideco. Он обращается к
`31.187.97.119` по IKEv2/NAT-T; AL-SPB-MILLION передаёт только UDP `500` и
`4500` на `172.31.146.2`. Такой путь не требует, чтобы СПБ Ideco умел
маршрутизировать к приватным адресам Москвы через старые корпоративные VPN.
На AL-SPB-MILLION предварительно не было соответствующего dst-NAT.

Откат после применения: удалить два правила dst-NAT/forward с комментарием
`Ideco S2S pilot MSK`, удалить обе VTI-записи и созданные алиасы сетей на
Ideco, затем отключить IPsec на узле, если других IPsec-подключений на нём не
появилось.

### Выполненная конфигурация и проверка 2026-08-05

Созданы две VTI-записи IPsec/IKEv2 с общим PSK и Key ID (секрет не хранится в
этом документе):

| Узел | Направление | Идентификатор Ideco | VTI-адрес | Сети |
| --- | --- | --- | --- | --- |
| СПБ `192.168.203.82` | входящее `device2utm` | `3ad90b87-dc56-432d-9b74-ee29d4bc311f` | `10.254.60.1/30` | local `10.76.146.0/24`, remote `10.77.0.0/24` |
| Москва `10.77.0.253` | исходящее `utm2device` к `31.187.97.119` | `d5e69c0b-104b-4f3a-96ee-2d80f81cd9a1` | `10.254.60.2/30` | local `10.77.0.0/24`, remote `10.76.146.0/24` |

На AL-SPB-MILLION добавлены только два правила с комментариями:

```routeros
/ip firewall nat add chain=dstnat action=dst-nat protocol=udp \
  dst-address=31.187.97.119 dst-port=500,4500 to-addresses=172.31.146.2 \
  comment="Ideco S2S pilot MSK IKEv2 dstnat"
/ip firewall filter add chain=forward action=accept in-interface-list=WAN \
  protocol=udp dst-address=172.31.146.2 dst-port=500,4500 \
  comment="Ideco S2S pilot MSK IKEv2 forward" place-before=[find where comment="drop forward"]
```

Глобальный IPsec и обе VTI включены. Проверка после включения: оба Ideco
показывают `state=established`; входящий адрес пира СПБ — `195.239.57.113`,
а на AL-SPB-MILLION увеличились счётчики обоих правил UDP 500/4500. С Ideco
СПБ подтверждены ICMP `10.254.60.1 → 10.254.60.2` и
`10.254.60.1 → 10.77.0.253` (0% потерь, около 13 мс). Маршрут
`10.77.0.253` выбирает VTI-интерфейс `Ipsec1682615901`.

Это подтверждает туннель и доступ к московскому Ideco. Для доступа **хостов**
из московской LAN к `10.76.146.0/24` их локальный шлюз должен знать обратный
маршрут `10.76.146.0/24 via 10.77.0.253`; в рамках этого шага он намеренно не
менялся.

### Точный откат S2S

Сначала отключить/удалить обе VTI в GUI Ideco (**Сервисы → IPsec**) по
идентификаторам выше, затем удалить добавленные сети-алиасы: на СПБ
`10.77.0.0/24`, на Москве `10.77.0.0/24` и `10.76.146.0/24` (не удалять
предсуществующий алиас Wi-Fi pilot СПБ `10.76.146.0/24`). После проверки, что
на каждом узле не осталось иных IPsec-профилей, выключить глобальный IPsec.

На AL-SPB-MILLION удалить только правила данного пилота:

```routeros
/ip firewall nat remove [find where comment="Ideco S2S pilot MSK IKEv2 dstnat"]
/ip firewall filter remove [find where comment="Ideco S2S pilot MSK IKEv2 forward"]
```

Перезагрузка, переподключение Wi-Fi и изменение существующих S2S-каналов для
отката не требуются.

## Подготовка перевода firewall Ideco СПБ на site allow-list (2026-08-05)

### Исходное состояние и границы изменения

В firewall Ideco СПБ включён пользовательский firewall, включён штатный
`forward_invalid_drop`, а автоматический SNAT выключен. До изменения в
таблице FORWARD есть одно широкое разрешающее правило:

```text
Wi-Fi pilot VLAN 1460 — application observation only
10.76.146.0/24 (Lvlan1460_2 / interface.id.2) → any
```

Оно было необходимо для первоначального DPI-наблюдения, но не соответствует
модели site-router: пользовательская зона не должна получать неявный доступ
ко всем корпоративным сетям.

Первый этап затрагивает **только** транзит из `10.76.146.0/24`. Он не меняет
IPsec, SNAT, DHCP, DNS, AD/web-авторизацию, интерфейсы и INPUT-правила самого
Ideco. Управляющий интерфейс `192.168.203.82/24` пока не имеет выделенной
административной зоны, поэтому его защита будет отдельным контролируемым
этапом после инвентаризации допустимых источников.

### Целевая последовательность FORWARD

1. `10.76.146.0/24 → Internet`: только через WAN `Eeth3`, с исключением
   корпоративных сетей `10.0.0.0/8` и `192.168.0.0/16`; DPI-наблюдение
   сохраняется.
2. `10.76.146.0/24 → approved corporate services`: только текущий набор
   `shared_srvs`, `spb-dc1-al` и корпоративный resolver.
3. `10.76.146.0/24 → 10.77.0.0/24`: тестовый Ideco S2S.
4. Финальный `drop` для остального трафика из VLAN 1460.

Эта последовательность повторяет принцип шаблона site-router: сначала
ролевые разрешения, затем Интернет, а доступ к прочим private/corporate
сетям отсутствует. Ответы на разрешённые соединения обрабатываются
системными stateful-правилами Ideco.

### Откат этапа

Удалить созданные три правила FORWARD и два алиаса private-сетей, затем
вернуть правило с исходным ID `1` к широкому `10.76.146.0/24 → any` с
комментарием `Wi-Fi pilot VLAN 1460 — application observation only`.
Идентификаторы созданных объектов и точные команды/запросы фиксируются ниже
после применения и проверки. Если необходимо немедленно восстановить
доступность, в локальном меню Ideco можно выбрать «Отключить пользовательский
файрвол»: системные правила при этом остаются активны.

### Применение 2026-08-05

Созданы алиасы:

```text
subnet.id.5  Site firewall: private 10/8       10.0.0.0/8
subnet.id.6  Site firewall: private 192.168/16 192.168.0.0/16
```

Широкое правило `FORWARD` ID `1` изменено, а следующие правила добавлены
после него в указанном порядке:

| ID | Действие | Назначение |
| ---: | --- | --- |
| 1 | allow + DPI | VLAN 1460 только в не-corporate Internet через `Eeth3`; назначения `10/8` и `192.168/16` исключены |
| 2 | allow | VLAN 1460 к 13 доступным алиасам `shared_srvs`, `spb-dc1-al` и корпоративному resolver через `Eeth3` |
| 3 | allow | VLAN 1460 к `10.77.0.0/24` через Ideco S2S |
| 4 | drop | остальной FORWARD-трафик из VLAN 1460 |

`10.10.20.50` (dc2) намеренно не входит в список: с пилотной сети у него нет
обратного пути. Отключённая запись `10.10.22.3` из `shared_srvs` также не
переносилась. Включён только счётчик пользовательских FORWARD-правил
(`firewall watch`); он не меняет решение firewall и нужен для проверки.

После применения подтверждены SSH к `192.168.203.82`, маршрут в `10.77.0.0/24`
через VTI и ICMP `10.254.60.1 → 10.254.60.2` без потерь. Проверка трафика
клиента VLAN 1460 и счётчиков правил выполняется отдельно.

### Точный откат applied-этапа

1. Сначала удалить правила `FORWARD` ID `2`, `3`, `4` в GUI **Правила
   трафика → Файрвол → FORWARD**.
2. Изменить правило ID `1`: назначение — `Любой`, исключение назначения
   выключить, исходящий интерфейс — `Любой`, комментарий вернуть к
   `Wi-Fi pilot VLAN 1460 — application observation only`.
3. Удалить алиасы `subnet.id.5` и `subnet.id.6` в **Правила трафика →
   Объекты → Сети**.
4. По завершении проверки при необходимости выключить счётчик срабатываний
   правил. IPsec, DHCP, DNS, SNAT и INPUT не менять.

## Подготовка INPUT-защиты Ideco СПБ (2026-08-05)

### Состояние до изменения

В пользовательской таблице INPUT нет правил. На сервере слушаются, среди
прочего, SSH `22/TCP`, веб-интерфейс `8443/TCP`, DNS `53/TCP,UDP`, DHCP
`67/UDP` на VLAN 1460, IKEv2/NAT-T `500,4500/UDP`, а также `80,443/TCP` для
web-auth/веб-служб. Прослушивание сокета не означает его обязательную
публикацию: защиту создают системные и пользовательские правила firewall.

В подтверждённый временный список администрирования войдут только:

```text
192.168.203.178/32  текущий управляющий хост
10.10.3.112/32      подтверждённый хост из журнала SSH
10.78.90.32/27      пул административного VPN
```

`10.76.146.135` — клиент тестового Wi-Fi; он не получает административного
доступа. Управление с WAN не публикуется. Текущий IPsec-пир Москва имеет
наблюдаемый публичный адрес `195.239.57.113/32`.

### План INPUT

1. DHCP: только VLAN 1460 → UDP/67.
2. Web-auth: только VLAN 1460 → TCP/80,443.
3. Управление: только список администраторов → TCP/22,8443, вход через Leth1.
4. IPsec: только московский публичный пир → UDP/500,4500, вход через Eeth3.
5. ICMP для диагностики/PMTU.
6. Финальный INPUT drop — включается последним после проверки SSH, GUI и S2S.

DNS на Ideco намеренно не разрешается: клиентам пилота задан корпоративный
resolver, а не адрес Ideco. Существующие системные stateful-правила Ideco
обрабатывают ответы на разрешённые соединения.

### Откат

Если после включения final drop недоступно управление, через локальную
консоль Ideco выбрать «Отключить пользовательский файрвол» — системные
правила останутся активны. После восстановления удалить только созданные
INPUT-правила и алиасы, перечисленные в разделе применения ниже; FORWARD,
IPsec, DHCP, DNS и SNAT не менять.

### Применение и проверка 2026-08-05

Созданы отдельные IP/сетевые/портовые алиасы для двух подтверждённых
управляющих хостов, admin VPN-пула, московского публичного IPsec-пира и
сервисов DHCP, SSH, веб-управления, IKEv2/NAT-T. В таблицу INPUT добавлены
в следующем порядке:

| ID | Действие | Назначение |
| ---: | --- | --- |
| 2 | allow | DHCP с VLAN 1460 на UDP/67 |
| 3 | allow | web-auth с VLAN 1460 на TCP/80,443 |
| 4 | allow | SSH/веб-управление только с утверждённого admin allow-list через Leth1 |
| 5 | allow | IKEv2/NAT-T только от `195.239.57.113` через Eeth3 |
| 6 | allow | ICMP для диагностики и PMTU |
| 7 | drop | финальный запрет всего прочего INPUT-трафика |

Правило ID `7` включено последним. После этого подтверждены новая независимая
сессия GUI (`HTTP 200`) и новая SSH-сессия без reuse соединения. Счётчик
правила управления ID `4` вырос до 12 пакетов, IPsec ID `5` — до 2 пакетов;
значит разрешения действительно участвуют в обработке. Final drop ID `7`
уже отбросил 4089 неразрешённых входящих пакетов. Изменений в FORWARD, IPsec,
DHCP, DNS, SNAT, интерфейсах или существующих пользователях не было.

### Точный откат INPUT

В GUI **Правила трафика → Файрвол → INPUT** сначала выключить правило ID `7`,
затем удалить правила `2`–`7`. После этого удалить объекты с названиями,
начинающимися на `Ideco input:`. Не удалять алиасы `subnet.id.1`–`subnet.id.7`,
которые используются другими частями пилота, кроме специально созданного
`subnet.id.7` (admin VPN pool): его можно удалить только после удаления
правила ID `4`.
