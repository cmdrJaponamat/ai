# PVE3: подготовка VLAN-интерфейсов резервных сетей Corosync

Дата: 2026-09-02. Узел: `spb-pve3` (`10.78.2.203`). Статус обновлён
2026-09-03: применено, оба физических линка подключены и проверены.

## Цель и граница

Подготовить PVE3 к будущему физическому подключению к уже подготовленным и
оставленным в `shutdown` портам H3C:

- `eno3.1060` — `10.78.6.3/29`, ring1 через H3C upper;
- `eno4.1061` — `10.78.6.11/29`, ring2 через H3C lower.

На этом шаге не меняются `/etc/pve/corosync.conf`, ring0, `bond0`, `vmbr0`,
default gateway, PVE1/PVE2, iSCSI, MSA и H3C. Новые интерфейсы не включаются
в bridge или bond.

## Подтверждённый baseline

Read-only проверка перед изменением:

- кластер `SPB-OBIT-DC` quorate, три голоса/три ноды, config version 12;
- Corosync использует только ring0 `10.78.2.201–203`, `link_mode: passive`;
- PVE3 management: `vmbr0 = 10.78.2.203/24`, gateway `10.78.2.254`,
  bridge использует `bond0` из `eno1/eno2`;
- `eno3` (`08:f1:ea:ed:d2:4e`) и `eno4` (`08:f1:ea:ed:d2:4f`) не входят в
  master-интерфейс, не имеют IP, физически `NO-CARRIER`;
- оба интерфейса — Broadcom BCM5719, драйвер `tg3`, максимум 1 Гбит/с,
  autonegotiation включён;
- исходные `eno3`/`eno4` уже описаны как `auto`/`manual`.

## Изменение

Через штатный Proxmox API (`pvesh`) создать два VLAN-интерфейса с autostart,
CIDR из таблицы выше и явными raw-device/VLAN ID. Сначала API создаёт pending
конфигурацию; перед её применением обязательны readback и проверка diff.

## Проверка

- pending-конфигурация меняет только два новых VLAN-интерфейса;
- после применения SSH management остаётся доступен;
- `pvecm status` остаётся quorate с тремя нодами;
- `ip -br addr` показывает новые адреса, а carrier отсутствует до подключения;
- default route, bond, bridges и `corosync.conf` не изменены.

Фактический результат:

- перед изменением создана резервная копия
  `/root/interfaces.pre-pve3-corosync-20260902` с правами `0600`;
- pending diff содержал только два новых VLAN-блока;
- штатная задача Proxmox network reload завершилась `exitstatus: OK`;
- `eno3.1060@eno3` имеет `10.78.6.3/29`, VLAN ID 1060 и состояние
  `LOWERLAYERDOWN`;
- `eno4.1061@eno4` имеет `10.78.6.11/29`, VLAN ID 1061 и состояние
  `LOWERLAYERDOWN`;
- default route остался `via 10.78.2.254 dev vmbr0`; добавились только две
  ожидаемые connected route со статусом `linkdown`;
- SSH management после reload доступен; кластер по-прежнему quorate: три
  ноды, три голоса, Corosync config version 12;
- `corosync-cfgtool -s` показывает только исходный link 0 и всех peers
  connected; ring1/ring2 в Corosync не добавлялись;
- failed systemd units отсутствуют; в журнале reload только два не связанных
  с изменением предупреждения о deprecated bridge `hash_elasticity`.

## Откат

Если конфигурация ещё pending — `pvesh delete /nodes/spb-pve3/network`.
После применения удалить только `eno3.1060` и `eno4.1061` через Proxmox API
или GUI, проверить pending diff и применить reload. При недоступности API
восстановить сохранённый `/root/interfaces.pre-pve3-corosync-20260902` с
локальной/BMC-консоли и выполнить штатный network reload.

## Перезапуск

Reboot и relogin не требуются. Порты H3C включаются только после физического
подключения и отдельной проверки маркировки; Corosync меняется позднее, когда
оба резервных кольца готовы на всех трёх узлах.

## Физическое подключение 2026-09-03

- `eno3.1060` — UP, `10.78.6.3/29`, carrier 1000 Мбит/с/full duplex;
  H3C upper изучил точный MAC `08:f1:ea:ed:d2:4e` в VLAN 1060 на `XGE1/0/5`;
- `eno4.1061` — UP, `10.78.6.11/29`, carrier 1000 Мбит/с/full duplex;
  H3C lower изучил точный MAC `08:f1:ea:ed:d2:4f` в VLAN 1061 на `XGE1/0/5`;
- RX/TX errors, drops и carrier errors на обоих PVE3-интерфейсах равны нулю;
- default route и management не изменились; кластер quorate, три ноды;
- Corosync остаётся на config version 12 и использует только link 0.

Ответы ping внутри новых `/29` пока не ожидаются: PVE1/PVE2 к VLAN 1060/1061
ещё не подключены. Добавлять ring1/ring2 в `corosync.conf` на этом этапе нельзя.

## Завершение проекта 2026-09-04

PVE1 и PVE2 подключены к обоим VLAN, полная матрица связности и MTU 1500
проверены без потерь. Corosync config version 13 содержит links 0/1/2; все
peers connected на каждом узле. Контролируемые отдельные отказы каждого link
на PVE3 прошли с сохранением quorum 3/3. Полный итог и откат:
`recovery/2026-09-04-corosync-multilink-completion-plan.md`.
