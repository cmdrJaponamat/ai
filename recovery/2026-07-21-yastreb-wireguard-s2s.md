# Yastreb WireGuard S2S

Date: 2026-07-21

## Scope

Raised WireGuard S2S for vessel `Yastreb` between:

- Site router: `AL-YASTREB-GW`, bench IP `10.10.30.23`
- Hub router: `AL-OBIT`, public endpoint `85.114.6.214`
- MMK transit router: `AL-MMK`, IP `10.10.30.1`

## WireGuard Parameters

- Hub interface: `WG-YASTREB`
- Site interface: `WG-DC-YASTREB`
- UDP port: `13240`
- Transport network: `10.254.32.0/30`
- Hub IP: `10.254.32.1/30`
- Site IP: `10.254.32.2/30`
- Site summary route: `10.32.0.0/16`

## Changes

On `AL-OBIT`:

- Added `WG-YASTREB`.
- Added `10.254.32.1/30`.
- Added `WG-YASTREB` to `VPN-STS`.
- Added input allow for UDP `13240` on WAN.
- Added peer for `AL-YASTREB-GW` with allowed addresses `10.254.32.2/32,10.32.0.0/16`.
- Added route `10.32.0.0/16` via `WG-YASTREB`, distance `20`.

On `AL-YASTREB-GW`:

- Added peer to `85.114.6.214:13240` on `WG-DC-YASTREB`.
- Enabled routes through `WG-DC-YASTREB`:
  - `10.78.0.0/16`
  - `10.10.0.0/16`
  - `192.168.0.0/16`
- Added temporary bench management route:
  - `10.10.40.149/32` via `10.10.30.1`

On `AL-MMK`:

- Added route `10.32.0.0/16` via `OVPN-OBIT`, distance `40`.
- Added route `10.32.0.0/16` via `WG-OBIT`, distance `50`.

## Backups

Pre-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-wg-prechange-al-obit/`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-wg-prechange-al-yastreb-gw/`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-route-prechange-al-mmk/`

Post-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-wg-postchange-al-obit/`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-wg-postchange-al-yastreb-gw/`
- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-wg-postchange-al-mmk/`

Each directory contains an export, binary backup, and `SHA256SUMS`.

## Verification

From `AL-YASTREB-GW`:

- WireGuard peer to hub showed a recent handshake.
- `ping 10.254.32.1 count=5`: 5/5 replies.
- `ping 10.78.3.50 count=3`: 3/3 replies.
- `ping 10.10.40.149 count=3`: 3/3 replies.

From `AL-OBIT`:

- Peer `yastreb site router` showed a recent handshake.
- `ping 10.254.32.2 count=5`: 5/5 replies.
- `ping 10.32.40.1 count=5`: 5/5 replies.
- `ping 10.32.44.1 count=3`: 3/3 replies.

From `AL-MMK`:

- Route `10.32.0.0/16` via `OVPN-OBIT` was active.
- Backup route via `WG-OBIT` was present.
- `ping 10.32.40.1 count=3`: 3/3 replies.

Note: direct ping from workstation `10.10.40.149` to `10.32.40.1` did not pass during bench verification, despite `AL-MMK` itself reaching the site. Router-to-router S2S is up; workstation reachability may require separate MMK forward/policy review if needed.

## Rollback

On `AL-YASTREB-GW`:

```routeros
/interface wireguard peers remove [find where comment="SPB DC hub" and interface=WG-DC-YASTREB]
/ip route disable [find where gateway=WG-DC-YASTREB and static]
/ip route remove [find where comment="TEMP bench admin workstation via AL-MMK before WG cutover"]
```

On `AL-OBIT`:

```routeros
/ip route remove [find where comment="yastreb via WG backup"]
/interface wireguard peers remove [find where comment="yastreb site router"]
/ip firewall filter remove [find where comment="Allow WG Yastreb"]
/interface list member remove [find where interface=WG-YASTREB]
/ip address remove [find where interface=WG-YASTREB]
/interface wireguard remove [find where name=WG-YASTREB]
```

On `AL-MMK`:

```routeros
/ip route remove [find where comment="yastreb via OBIT primary"]
/ip route remove [find where comment="yastreb via OBIT WG backup"]
```

Binary backups listed above can be restored if command rollback is not enough.
