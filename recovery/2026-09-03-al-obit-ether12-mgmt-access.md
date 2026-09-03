# AL-OBIT: ether12 как untagged access-порт management VLAN 1000

Дата: 2026-09-03. Устройство: `AL-OBIT` (`10.78.3.254`). Статус: применено
и проверено.

## Проблема и цель

`ether12` предназначен для временного подключения запасного MikroTik, чтобы
тот мог получить адрес из management DHCP. До изменения порт имел `pvid=1`,
но был указан tagged-членом VLAN 1000. Обычный нетегированный endpoint поэтому
не попадал в management VLAN.

Цель: сделать `ether12` обычным access-портом VLAN 1000:

- ingress untagged -> PVID 1000;
- egress VLAN 1000 -> untagged;
- tagged пользовательские кадры на access-порту не принимать.

## Подтверждённый baseline

- `ether12` входит в `bridge`, `pvid=1`, `ingress-filtering=yes`,
  `frame-types=admit-all`;
- VLAN 1 динамически untagged на `bridge,LAG-SW,ether12`;
- статическая запись VLAN 1000: tagged `bridge,LAG-SW,ether12`, untagged
  `ether3,ether4,ether5,ether6,ether7,ether8,ether9,ether10,ether11`;
- DHCP `vlan1000(mgmt)-dhcp` активен на `VLAN1000-MGMT-INFRA`;
- сеть `10.78.0.0/24`, пул `10.78.0.100-10.78.0.253`, gateway/DNS
  `10.78.0.254`, lease time 30 минут.

## Изменение

Перед изменением сохранить на роутере binary backup и hide-sensitive export.
В статической bridge VLAN-записи 1000 удалить `ether12` из tagged и добавить в
untagged. На bridge-port `ether12` задать `pvid=1000` и
`frame-types=admit-only-untagged-and-priority-tagged`.

## Проверка

- `ether12` показывает PVID 1000 и access frame policy;
- VLAN 1000 показывает `ether12` только в untagged/current-untagged;
- VLAN 1 больше не содержит `ether12`;
- management DHCP остаётся active;
- SSH к AL-OBIT через Admin VPN остаётся доступен.

После возврата запасного MikroTik на порт проверить DHCP lease/MAC отдельно.
Наличие DHCP-сервера не гарантирует lease, если на запасном MikroTik нет
DHCP-клиента на подключённом порту/bridge.

## Откат

Вернуть VLAN 1000: tagged `bridge,LAG-SW,ether12`, untagged только
`ether3-ether11`; вернуть bridge-port `ether12` к `pvid=1`,
`frame-types=admit-all`. При необходимости восстановить router backup/export
`pre-ether12-mgmt-access-20260903` с локальной консоли.

Relogin/reboot не требуются.

## Фактический результат

- на AL-OBIT сохранены `pre-ether12-mgmt-access-20260903.backup` и
  `pre-ether12-mgmt-access-20260903.rsc`;
- `ether12`: `pvid=1000`, `ingress-filtering=yes`,
  `frame-types=admit-only-untagged-and-priority-tagged`;
- VLAN 1000: tagged только `bridge,LAG-SW`, `ether12` находится в
  untagged/current-untagged;
- динамический VLAN 1 больше не содержит `ether12`;
- DHCP `vlan1000(mgmt)-dhcp` остался active;
- повторный SSH-readback AL-OBIT через Admin VPN успешен.

Следующая проверка выполняется после соединения запасного MikroTik с
`AL-OBIT ether12`: найти его MAC и DHCP lease. Если lease не появляется,
проверить DHCP client на соответствующем интерфейсе/bridge запасного роутера.
