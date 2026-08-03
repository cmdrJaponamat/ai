# Admin VPN gateway ACL and Yastreb enrollment

## Objective

Permit the administrative OpenVPN pool 10.78.90.32/27 to manage and route through
corporate gateway MikroTik devices, and enroll the vessel gateway AL-YASTREB-GW.

## Parallel client tunnel

The active NetworkManager profile admin-vpn-parallel uses tun1 and received static
CCD address 10.78.90.34/27. It deliberately has never-default=yes and
ignore-auto-dns=yes, with the existing Wi-Fi DNS retained. The independent manual tunnel
uses tun0 and was not restarted or modified.

To stop only the parallel client tunnel:

    nmcli connection down id admin-vpn-parallel

## Applied gateway rules

The following two comments identify the only new RouterOS filter rules:

- CORP: Admin VPN 10.78.90.32/27 input
- CORP: Admin VPN 10.78.90.32/27 forward

They were installed immediately before the final drop of their respective chain on:

- AL-OBIT
- AL-MMK
- MSK-office
- AL-SPB-MILLION
- AL-SPB-Remeslennaya
- AL-MMRP
- AL-KBO
- AL-MZTO
- AL-NU

The rules accept only source 10.78.90.32/27. They do not modify NAT, routing,
address lists, VPN configuration, or existing firewall rules.

## Not changed

AL-KRR, AL-MMK-GPNS and AL-YASTREB-GW rejected available SSH administrator
credentials. No password guessing, access bypass, or firewall change was performed on them.
Their rules need to be added after their current full administrative credentials are verified.

## Yastreb

- Oxidized production source now includes 10.254.32.2:routeros.
- Backup of the previous router.db is
  /home/oxidized/.config/oxidized/router.db.backup-20260803-yastreb on spb-oxidized.
- PortalAL catalogue contains gw-yastreb, visible only to the admin role.

## Rollback

On each changed gateway:

    /ip firewall filter remove [find where comment="CORP: Admin VPN 10.78.90.32/27 input"]
    /ip firewall filter remove [find where comment="CORP: Admin VPN 10.78.90.32/27 forward"]

For Oxidized, restore the named router.db backup and restart oxidized.service.
For PortalAL, remove only gw-yastreb from its managed baseline and catalogue.
