# MikroTik 10.10.30.23 Yastreb Site32 Config

Date: 2026-07-21

## Scope

Configured the MikroTik hAP ac2 bench router at `10.10.30.23` for vessel `Yastreb`.

- Identity: `AL-YASTREB-GW`
- Site octet: `32`
- Site summary: `10.32.0.0/16`
- RouterOS: `7.12.1`
- Board: `hAP ac2` / `RBD52G-5HacD2HnD`
- Serial: `HCY08A3VK28`

## Access

- Added `ansible` user with `full` group using the MikroTik vault password.
- Left default `admin` user in place for manual disable/removal later.
- Temporary bench access remains on `ether1` via DHCP in `10.10.30.0/24`.
- SSH/Winbox allowed from admin networks, `10.10.40.149/32`, trusted public admin IPs, OpenVPN admin pool, and temporary `10.10.30.0/24`.

## Applied Network Layout

`ether1` is temporary bench/uplink DHCP and future vessel WAN.

`ether2` is the LAN tagged trunk to the vessel site switch.

Configured VLAN gateways:

- VLAN 1400 users: `10.32.40.1/24`
- VLAN 1440 AP management: `10.32.44.1/24`
- VLAN 1450 guest Wi-Fi: `10.32.45.1/24`
- VLAN 1470 CCTV cameras: `10.32.47.1/24`
- VLAN 1480 CCTV NVR: `10.32.48.1/24`
- VLAN 1490 ACS: `10.32.49.1/24`
- VLAN 1500 voice: `10.32.50.1/24`
- VLAN 1510 print devices: `10.32.51.1/24`
- VLAN 1520 print services: `10.32.52.1/28`

WireGuard interface `WG-DC-YASTREB` was created with local address `10.254.32.2/30`, but no peer was added during this step.

Static corporate routes via `WG-DC-YASTREB` were disabled after import because a route to `10.10.0.0/16` through an empty WireGuard interface broke return traffic to the admin workstation. Enable or replace these routes only after the real WireGuard peer and routing design are in place.

## Backups

Pre-config backup:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site32-config/10.10.30.23-pre-site32-config.rsc`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site32-config/pre-site32-config.backup`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site32-config/SHA256SUMS`

Post-config backup:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-yastreb-site32-config/10.10.30.23-yastreb-site32-config.rsc`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-yastreb-site32-config/yastreb-site32-config.backup`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-yastreb-site32-config/SHA256SUMS`

## Incident During Import

After importing the site config, management from `10.10.40.149` was temporarily lost. DHCP on `AL-MMK` still showed `10.10.30.23` bound with hostname `AL-YASTREB-GW`, proving the device was alive.

Root cause: placeholder route `10.10.0.0/16` via `WG-DC-YASTREB` was active even though no WireGuard peer existed. Replies to `10.10.40.149` followed that route and disappeared.

Temporary recovery action:

1. Added a short-lived srcnat rule on `AL-MMK` for `10.10.40.149 -> 10.10.30.23`, making management traffic appear from `10.10.30.1`.
2. Connected to `AL-YASTREB-GW`.
3. Disabled static placeholder routes via `WG-DC-YASTREB`.
4. Removed the temporary srcnat rule from `AL-MMK`.

## Verification

- `ping -c 3 10.10.30.23`: 3/3 replies.
- SSH as `ansible` to `10.10.30.23`: successful.
- `/system identity print`: `AL-YASTREB-GW`.
- `/system resource print`: RouterOS `7.12.1`, hAP ac2.
- `/ip route print where gateway=WG-DC-YASTREB`: static corporate routes are disabled.
- `AL-MMK` DHCP lease for `10.10.30.23`: bound, hostname `AL-YASTREB-GW`.
- Temporary `AL-MMK` srcnat rule with comment `TEMP-CODEX-YASTREB-MGMT-SRCNAT remove after site config fix`: removed.

## Rollback

Restore the pre-config binary backup:

`/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site32-config/pre-site32-config.backup`

If the device is unreachable over IP, use physical access with Winbox/Netinstall and restore the binary backup from the same directory.
