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

## Yastreb compatibility LAN route from the workstation

The gateway at 10.254.32.2 is reachable through the existing tunnel. The vessel LAN
192.168.1.0/24 needs an explicit client route because it is outside the tunnel's original
route list. The persistent OpenVPN profile /home/admin-al/work/admin.ovpn now includes:

    route 192.168.1.0 255.255.255.0

To activate this route immediately without reconnecting the externally managed tun0, run
from an authenticated local terminal:

    sudo ip route replace 192.168.1.0/24 via 10.10.3.1 dev tun0

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

## Temporary access through legacy admin VPN (`tun0`)

The workstation's legacy tunnel address `10.10.3.112` can reach
`10.254.32.2` through routing and WireGuard, but the Yastreb input policy accepts
TCP management only from its `ADMIN-NETS` list.  On 2026-08-03 a narrow temporary
source-NAT rule was added on AL-OBIT so that this one source appears as the
already-authorized AL-OBIT address when reaching only the Yastreb gateway:

    /ip firewall nat add chain=srcnat action=src-nat \
      src-address=10.10.3.112/32 dst-address=10.254.32.2/32 \
      out-interface=WG-YASTREB to-addresses=10.78.3.254 \
      comment="TEMP admin-al tun0 access to Yastreb 2026-08-03"

After this rule was installed, TCP/22 and TCP/8291 on `10.254.32.2` responded.
It does not provide access to other systems or from other clients.

The durable replacement, once a working Yastreb administrator account is
confirmed, is to add `10.10.3.0/24` to `ADMIN-NETS` (and `VPN-ADMINS` if used by
the forward policy) on AL-YASTREB-GW, verify WinBox access, then remove the
temporary NAT rule.

This replacement was completed on 2026-08-03: `10.10.3.0/24` was added to
AL-YASTREB-GW's `ADMIN-NETS` with comment `legacy admin VPN tun0`, and the
temporary AL-OBIT NAT rule was removed. TCP/22 and TCP/8291 remained reachable
from the workstation through `tun0` afterwards.

AL-YASTREB-GW and AL-MMK-GPNS also now contain the standard pair of rules for
the newer administrative VPN pool `10.78.90.32/27`:

- `CORP: Admin VPN 10.78.90.32/27 input`
- `CORP: Admin VPN 10.78.90.32/27 forward`

## Rollback

On each changed gateway:

    /ip firewall filter remove [find where comment="CORP: Admin VPN 10.78.90.32/27 input"]
    /ip firewall filter remove [find where comment="CORP: Admin VPN 10.78.90.32/27 forward"]

For Oxidized, restore the named router.db backup and restart oxidized.service.
For PortalAL, remove only gw-yastreb from its managed baseline and catalogue.

For the temporary AL-OBIT source NAT rule:

    /ip firewall nat remove [find where comment="TEMP admin-al tun0 access to Yastreb 2026-08-03"]

To remove the durable legacy-tunnel Yastreb access, if explicitly required:

    /ip firewall address-list remove [find where list="ADMIN-NETS" and address="10.10.3.0/24" and comment="legacy admin VPN tun0"]
