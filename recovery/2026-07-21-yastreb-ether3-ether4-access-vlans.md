# Yastreb Ether3/Ether4 Access VLANs

Date: 2026-07-21

## Scope

Configured access ports on `AL-YASTREB-GW` (`10.10.30.23`):

- `ether3`: untagged/access VLAN `1400` users, `10.32.40.0/24`
- `ether4`: untagged/access VLAN `1440` AP/service management, `10.32.44.0/24`

Existing `ether2` tagged trunk and service Wi-Fi on VLAN `1440` were kept.

## Backups

Pre-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-ether3-ether4-access-prechange/`

Post-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-ether3-ether4-access-postchange/`

Each directory contains export, binary backup, and `SHA256SUMS`.

## Verification

- `ether3` bridge port has `pvid=1400`, untagged/prio-tagged only.
- `ether4` bridge port has `pvid=1440`, untagged/prio-tagged only.
- Bridge VLAN `1400`: tagged `bridge-LAN,ether2`, untagged `ether3`.
- Bridge VLAN `1440`: tagged `bridge-LAN,ether2`, untagged `wlan1,wlan2,ether4`.
- DHCP servers for `vlan1400-users` and `vlan1440-ap-mgmt` are enabled.
- Management access to `10.10.30.23` remained available; ping 3/3.

Ports were inactive during verification because no physical link was connected to `ether3`/`ether4`.

## Rollback

```routeros
/interface bridge port remove [find where interface=ether3]
/interface bridge port remove [find where interface=ether4]
/interface bridge vlan set [find where bridge=bridge-LAN and vlan-ids=1400] tagged=bridge-LAN,ether2 untagged="" comment="users/corp wifi trunk"
/interface bridge vlan set [find where bridge=bridge-LAN and vlan-ids=1440] tagged=bridge-LAN,ether2 untagged=wlan1,wlan2 comment="ap management trunk + TEMP service WiFi"
/interface ethernet set [find default-name=ether3] comment=reserved
/interface ethernet set [find default-name=ether4] comment=reserved
```

Binary restore option:

`/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-ether3-ether4-access-prechange/yastreb-pre-ether3-ether4-access.backup`
