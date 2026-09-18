# Ideco Client: bootstrap через публичный endpoint из Aurora-Corp

Дата: 2026-08-28, MSK  
Устройства: `IDECO-SPB-PILOT` (`192.168.203.82`) и `AL-SPB-MILLION` (`192.168.203.1`)  
Зона: `Aurora-Corp`, VLAN 1400, `10.76.40.0/24`

## Текущее состояние диагностики

Клиент использует единственное имя `ngfw.aurora-logistics.ru`, которое
резолвится во внешний адрес `31.187.97.119`. Профиль не переключается на
`10.76.40.1` и не зависит от внутренней DNS-зоны или Unbound.

Все ранее созданные экспериментальные правила удалены:

- на AL-SPB-MILLION нет правил с комментарием `Ideco Client hairpin`;
- на Ideco нет созданных для эксперимента alias `subnet.id.13`/`subnet.id.14`,
  DNAT/SNAT-записей и INPUT-записей 13/15.

Для диагностики целостного пути временно добавлены только следующие узкие
исключения:

- на Ideco — runtime-маршрут `31.187.97.119/32` через `172.31.146.1` в policy
  table Aurora-Corp и runtime iptables ACCEPT для
  `10.76.40.0/24 → 31.187.97.119` во всех протоколах;
- на AL-SPB-MILLION — INPUT ACCEPT для
  `10.76.40.0/24 → 31.187.97.119` с комментарием
  `DIAG: Aurora-Corp to NGFW public IP`.

Проверка пакетов с `10.76.40.147` подтвердила двусторонний ICMP и полное TCP/TLS
соединение до `ngfw.aurora-logistics.ru` (`31.187.97.119:443`): SYN, SYN/ACK,
TLS и полезные данные проходят в обе стороны.

Свежий лог клиента показал HTTP `511 Network Authentication Required` именно на
WebSocket handshake. После RouterOS DNAT соединение приходит на транзитный адрес
Ideco `172.31.146.2`; до исправления этот адрес отсутствовал в штатном наборе
`Ресурсы без авторизации`, поэтому его перехватывал transparent proxy.
Создан alias `ip.id.18` `IDECO-TRANSIT-PUBLIC-ENDPOINT` (`172.31.146.2`) и
добавлен в существующий набор ресурсов без авторизации. Runtime ipset
`noauth_resources` содержит этот адрес, а правило `squid_tproxy` теперь
пропускает его до Agent без captive-ответа 511.

## Отменённые попытки

На `AL-SPB-MILLION` кратковременно проверялась hairpin-схема. Все четыре
созданные для неё правила были удалены. На маршрутизаторе не осталось ни
одного правила с комментарием `Ideco Client hairpin`; действующие правила
публичной публикации Ideco не менялись.

Отдельное INPUT-разрешение прямого доступа к `10.76.40.1:443` (record 13)
также удалено: оно не соответствует целевой модели внешнего имени.

## Проверка и откат

До экспериментов сохранены:

- экспорт MikroTik: `AL-SPB-MILLION-prechange.rsc` в этой папке;
- состояние Ideco до изменения firewall/NAT:
  `/var/lib/ideco-support/20260828-agent-public-endpoint-bootstrap/`.

## Удаление временной диагностики

На Ideco выполнить:

```bash
iptables -D forward_sys_rules -i Lvlan112 -s 10.76.40.0/24 -d 31.187.97.119 \
  -m comment --comment "DIAG Aurora-Corp to public NGFW" -j ACCEPT
ip route del 31.187.97.119/32 via 172.31.146.1 dev Eeth4 table 60112
```

На AL-SPB-MILLION удалить только правило с комментарием
`DIAG: Aurora-Corp to NGFW public IP`.

Перезагрузка Ideco или маршрутизатора не требуется; runtime-правила Ideco также
исчезнут при пересборке firewall или перезагрузке.

## Откат штатного исключения Agent

На Ideco восстановить из
`/var/lib/ideco-support/20260828-agent-public-bootstrap-noauth/` значения
`ip-addresses.count.before` и `noauth-resource-1.before`, затем удалить
`/aliases/addresses/ip_addresses/v3/records/18`. Это вернёт прозрачный proxy для
транзитного адреса и воспроизведёт HTTP 511 для неавторизованного локального
клиента, поэтому выполнять только при отказе от данной схемы доступа.
