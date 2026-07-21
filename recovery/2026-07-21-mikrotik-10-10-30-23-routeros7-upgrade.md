# MikroTik 10.10.30.23 RouterOS 7 Upgrade

Date: 2026-07-21

## Problem Statement

Device `10.10.30.23` needs to be configured by the current MikroTik site-router template.

The active template requires RouterOS 7.x because it includes WireGuard and RouterOS 7 syntax. The device was running RouterOS `6.48.6 long-term`.

## Findings

- Address: `10.10.30.23`
- Model: `MikroTik hAP ac2` / `RBD52G-5HacD2HnD`
- Serial: `HCY08A3VK28`
- Initial RouterOS: `6.48.6 long-term`
- Initial RouterBOARD firmware: `6.48.6`
- Current config was near default:
  - DHCP client on `ether1`
  - dynamic address `10.10.30.23/24`
  - identity `RouterOS`
  - `admin` had no password
- Flash free space was very low before upgrade, about `2 MiB`, but built-in package update completed successfully.

## Exact Changes Made

1. Saved pre-upgrade export and binary backup:
   - `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site-template/10.10.30.23-pre-site-template.rsc`
   - `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site-template/pre-site-template.backup`
   - SHA256SUMS saved in the same directory.
2. Set update channel to `upgrade`.
3. Ran `/system package update install`.
4. Device upgraded to RouterOS `7.12.1 stable` and rebooted.
5. Ran `/system routerboard upgrade`.
6. Rebooted the device again.
7. Saved post-upgrade export and binary backup:
   - `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-post-routeros7-upgrade/10.10.30.23-post-routeros7-upgrade.rsc`
   - `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-post-routeros7-upgrade/post-routeros7-upgrade.backup`
   - SHA256SUMS saved in the same directory.

## Verification Status

Passed:

- ICMP to `10.10.30.23` after package upgrade reboot.
- ICMP to `10.10.30.23` after RouterBOARD firmware reboot.
- `/system resource print` shows:
  - `version: 7.12.1 (stable)`
  - `board-name: hAP ac2`
- `/system routerboard print` shows:
  - `current-firmware: 7.12.1`
  - `upgrade-firmware: 7.12.1`
- Post-upgrade export and binary backup saved locally.

## Rollback Strategy

Primary rollback:

- Restore `pre-site-template.backup` from:
  `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-10.10.30.23-pre-site-template/pre-site-template.backup`

If the device does not boot or cannot be reached:

- Use MikroTik Netinstall and then restore the saved backup/export manually.

## Relogin / Restart / Reboot

- Router reboot completed twice:
  - once after RouterOS package upgrade
  - once after RouterBOARD firmware upgrade
- No workstation relogin or reboot required.

## Next Steps

- Do not apply the site-router template until site variables are confirmed:
  - `SITE_NAME`
  - `SITE_SLUG`
  - `SITE_OCTET`
  - `SITE_SUMMARY`
  - WAN mode/address/gateway
  - OVPN credentials and transport subnet
  - WireGuard hub/site transport subnet and keys
- Set a real admin password or bootstrap the managed `ansible` user before leaving the device in production.
- Render the RouterOS 7 site template from:
  `/home/admin-al/assistant/notes/projects/global-network/site-router-template/`
