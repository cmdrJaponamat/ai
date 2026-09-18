# Ideco Client: local Aurora-Corp hairpin after full-tunnel SNAT

Дата: 2026-08-31, MSK  
Устройства: `IDECO-SPB-PILOT` (`192.168.203.82`) и `AL-SPB-MILLION` (`192.168.203.1`)  
Зона: Aurora-Corp, VLAN 1400, `10.76.40.0/24`

## Причина

После включения full tunnel и автоматического SNAT Ideco подменял источник
локального клиента при обращении к публичному имени
`ngfw.aurora-logistics.ru` (`31.187.97.119`) на транзитный адрес. Это
создавало петлю до RouterOS DNAT, поэтому клиент не мог начать VPN-сессию.

## Применённое решение

На Ideco добавлено runtime-исключение перед automatic MASQUERADE:

```bash
iptables -t nat -I POSTROUTING 2 -s 10.76.40.0/24 -d 31.187.97.119/32 \
  -o Eeth4 -m comment --comment "Ideco Client Aurora-Corp hairpin no-SNAT" -j ACCEPT
```

Оно действует только при обращении Aurora-Corp к публичному endpoint NGFW и
не разрешает иной неавторизованный интернет-трафик. Правило runtime-only:
после перезагрузки или пересборки firewall его нужно вернуть либо оформить
штатным исключением после отдельной проверки возможностей Novum.

На `AL-SPB-MILLION` сохранены перманентные hairpin правила:

- расширены существующие TCP правила `Ideco Client Aurora-Corp public endpoint
  dstnat` и `... return SNAT` до портов `80,443,14765`;
- добавлены `Ideco Client Aurora-Corp hairpin dstnat` (FORWARD accept с
  `connection-nat-state=dstnat`) и `... hairpin return SNAT`.

Они ограничены источником `10.76.40.0/24`, транзитным интерфейсом
`vlan1461-ideco-transit` и адресом Ideco `172.31.146.2`; return SNAT использует
`172.31.146.1`.

## Проверка

После удаления старых conntrack состояний клиента `10.76.40.147`:

- TCP `10.76.40.147 -> 31.187.97.119:443` установлен с ответом;
- UDP `:49238 -> :3051` двусторонний и `[ASSURED]`;
- peer `LagentWG_srv` имеет свежий handshake, адрес туннеля `10.128.0.2`.

## Откат

На Ideco:

```bash
iptables -t nat -D POSTROUTING -s 10.76.40.0/24 -d 31.187.97.119/32 \
  -o Eeth4 -m comment --comment "Ideco Client Aurora-Corp hairpin no-SNAT" -j ACCEPT
```

На RouterOS удалить только правила с комментариями:

- `Ideco Client Aurora-Corp hairpin dstnat`;
- `Ideco Client Aurora-Corp hairpin return SNAT`.

При необходимости вернуть прежний охват TCP-правил к `443`:

```routeros
/ip firewall filter set [find where comment="Ideco Client Aurora-Corp public endpoint dstnat"] dst-port=443
/ip firewall nat set [find where comment="Ideco Client Aurora-Corp public endpoint return SNAT"] dst-port=443
```
