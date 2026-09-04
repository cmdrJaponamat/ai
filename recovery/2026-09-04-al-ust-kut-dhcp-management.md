# AL-UST-KUT: DHCP management on SPB Million

Date: 2026-09-04

## Problem

New router `AL-UST-KUT` needed a management IPv4 while connected at SPB Million.

## Findings

- Device: MikroTik RB5009UPr+S+, RouterOS 7.20.7 long-term.
- Device MAC visible in MNDP/LLDP: `D0:EA:11:57:F7:E0`, router interface `ether2`.
- Physical path is `SPB-SW-410 ether13`, not a local port on SPB-SW-409.
- SW-409 sees the MAC only through its uplink to AL-SPB-MILLION.
- SW-410 ether13 is access/untagged VLAN 30, link 1 Gbit/s full duplex.
- AL-SPB-MILLION DHCP server `dhcp1` is active on VLAN 30 with pool `192.168.203.11-192.168.203.253`.
- No DHCP request, lease or ARP entry from the router MAC existed before the change.

## Change

- On AL-SPB-MILLION created static DHCP lease `192.168.203.9` for MAC
  `D0:EA:11:57:F7:E0`, client-id `1:d0:ea:11:57:f7:e0`, comment
  `AL-UST-KUT RB5009 ether2 management`.
- Before the change saved `pre-al-ust-kut-dhcp-20260904.rsc` and
  `pre-al-ust-kut-dhcp-20260904.backup` on AL-SPB-MILLION.
- Briefly disabled and enabled only SW-410 ether13 to trigger DHCP negotiation.

## Verification

- Port returned to link-ok, 1 Gbit/s full duplex.
- Lease remains `waiting`, `last-seen=never`.
- `192.168.203.9` does not answer ICMP and has no complete ARP record.
- Conclusion: server-side reservation is ready, but the DHCP client is not
  requesting on the connected `ether2`/bridge path.

## Next step

Using local Winbox/MAC access on AL-UST-KUT, inspect `/ip dhcp-client print detail`.
Move or add the DHCP client to the interface that contains connected ether2
(normally the LAN bridge), then renew it. Do not add another DHCP server to VLAN 30.

## SW-410 Ideco pilot cleanup

After explicit approval, the obsolete pilot-only VLAN entries `1460` and `1461`
were removed from SPB-SW-410. Before the change the switch saved
`pre-remove-ideco-pilot-20260904.rsc` and `.backup` locally. `ether11` was
returned to ordinary VLAN30 access settings. `ether13`, where AL-UST-KUT is
currently connected, is also restricted to untagged VLAN30 access.

Live LLDP/MNDP identifies the currently connected router side as
`bridge-LAN/ether1`, MAC `D0:EA:11:57:F7:DF`. The generated site-router template
uses `ether1` as a tagged LAN trunk, so it does not run a DHCP client or accept
the untagged VLAN30 address on that interface. To consume the prepared DHCP
lease, connect a template interface carrying a DHCP client (WAN or BENCH as
selected in its render variables) to this access port.

## Rollback

Remove only the DHCP lease whose comment is
`AL-UST-KUT RB5009 ether2 management`. No reboot or relogin is required.

## Final DHCP result

After moving the cable to the generated template's `BENCH_INTERFACE` `ether8`,
the router immediately requested DHCP as MAC `D0:EA:11:57:F7:E6`, hostname
`AL-UST-KUT`, and received `192.168.203.203`. The dynamic lease was converted
to a static lease with comment `AL-UST-KUT RB5009 ether8 TEMP bench`.

The earlier waiting reservation `192.168.203.9` for ether2 MAC
`D0:EA:11:57:F7:E0` was removed. A narrowly scoped temporary source-NAT rule
was tested for SSH bootstrap, did not bypass the router management allow-list,
and was removed immediately. No temporary NAT rule remains.

Current rollback is to remove only the static `.203` lease when temporary bench
management is no longer required. No reboot is required.

## Completion of Ust-Kut migration

The live configuration confirmed that site octet `18` was already rendered on
all nine site VLAN gateways and DHCP pools. The stale `YASTREB` references were
an unfinished DC/S2S preparation, not evidence that octet 18 belonged to
Yastreb. The registry now reserves `18` for Ust-Kut and retains `32` for
`AL-YASTREB-GW`.

Before the S2S changes, new local backups and hide-sensitive exports were saved:

- AL-OBIT: `pre-ust-kut-finish-20260904.backup/.rsc`;
- AL-UST-KUT: `pre-ust-kut-final-migration-20260904.backup/.rsc`.

Changes on AL-OBIT:

- renamed the disabled `WG-SITE` placeholder to `WG-UST-KUT`;
- assigned UDP `13226` and transport `10.254.18.1/30`;
- created its peer for site public key, `10.254.18.2/32` and `10.18.0.0/16`;
- enabled the matching input rule on UDP/13226;
- corrected site routes to OVPN distance 10 and WireGuard distance 20;
- renamed OVPN profile/secret from the stale Yastreb/generic names to
  `ovpn-UST-KUT` / `ovpn-ust-kut` without changing the stored password.

Changes on AL-UST-KUT:

- OVPN now authenticates as `ovpn-ust-kut`; stale Yastreb comments removed;
- WireGuard renamed to `WG-DC-UST-KUT`, moved from the conflicting
  `10.254.31.2/30`/UDP13239 values to `10.254.18.2/30`/UDP13226, pointed to the
  matching AL-OBIT public key, and enabled;
- primary/backup routes at distance 10/20 now cover `10.78.0.0/16`,
  `10.10.0.0/16`, `192.168.0.0/16`, and the existing `10.77.0.0/16`;
- restored the intended management allow-list for `10.78.0.0/16`, the admin
  workstation and Admin VPN pool;
- removed the temporary VLAN30 SSH firewall exception and its
  `192.168.203.0/24` address-list entry; SSH/Winbox service ACL no longer
  includes VLAN30.

Verification:

- OVPN is running at `10.252.18.2`; both tunnel endpoints answer with 0% loss;
- WireGuard has a current handshake and bidirectional counters;
- AL-OBIT reaches `10.18.40.1` with 0% loss;
- disabling OVPN moved the site route to WireGuard and retained 4/4 replies
  from `10.78.3.254`; re-enabling OVPN restored it as active primary;
- SSH to `AL-UST-KUT` succeeds through `10.18.40.1` after staging access was
  removed;
- Wiki.js page `it/network/site-octets` was updated successfully (page id 74).

The bench DHCP client on ether8 and its VLAN30 lease remain intentionally: they
currently provide Internet while the real provider settings on ether2 are still
unknown. The static provider placeholder must not be enabled until Ust-Kut WAN
address, prefix and gateway are confirmed. At physical deployment, connect the
provider to ether2, verify both S2S tunnels, then disable/remove ether8 from WAN
and remove the static lease on AL-SPB-MILLION.

Rollback: restore the named backups from local/console access. A targeted manual
rollback is to disable `WG-UST-KUT`, restore the previous OVPN names, and revert
the two `10.18.0.0/16` routes; do not touch the independent `WG-YASTREB` or
`WG-VITIM2`. No reboot or relogin is required.
