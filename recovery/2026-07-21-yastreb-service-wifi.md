# Yastreb Service Wi-Fi

Date: 2026-07-21

## Scope

Enabled temporary service Wi-Fi on `AL-YASTREB-GW` (`10.10.30.23`) for local setup access during vessel deployment.

## Configuration

- SSID: `AL-YASTREB-SVC`
- Security: WPA2-PSK, AES
- Radio `wlan1`: 2.4 GHz, `2447/20`, AP bridge
- Radio `wlan2`: 5 GHz, `5180/20-Ce`, AP bridge
- Regulatory domain: `russia`, indoor
- WPS: disabled
- Client forwarding: disabled
- Bridge: `bridge-LAN`
- Access VLAN: `1440` / `10.32.44.0/24`
- DHCP: existing `dhcp-ap-mgmt`, pool `pool-ap-mgmt`
- Router management: temporarily allowed from `10.32.44.0/24` through `ADMIN-NETS`, `TEMP-MGMT`, and `/ip service` address restrictions.

The Wi-Fi password is intentionally not stored in this recovery note or in git.

## Backups

Pre-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-service-wifi-prechange/`

Post-change:

- `/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-service-wifi-postchange/`

Each directory contains an export, binary backup, and `SHA256SUMS`.

## Verification

- `wlan1` status: `running-ap`
- `wlan2` status: `running-ap`
- VLAN `1440` bridge table includes `wlan1,wlan2` as untagged ports.
- `10.32.44.0/24` is present in `ADMIN-NETS` and `TEMP-MGMT`.
- `/ip service` SSH and Winbox allow `10.32.44.0/24`.
- DHCP server `dhcp-ap-mgmt` is active on `vlan1440-ap-mgmt`.

No client association test was performed from this workstation.

## Rollback

Disable service Wi-Fi:

```routeros
/interface wireless disable wlan1,wlan2
/interface bridge port remove [find where comment="TEMP service WiFi access VLAN1440"]
/interface bridge vlan set [find where bridge=bridge-LAN and vlan-ids=1440] tagged=bridge-LAN,ether2 untagged="" comment="ap management trunk"
/ip firewall address-list remove [find where comment="TEMP service WiFi management VLAN1440"]
/ip service set ssh address=10.78.0.0/16,10.10.40.149/32,10.78.90.32/27,95.54.192.18/32,31.187.97.119/32,10.10.30.0/24
/ip service set winbox address=10.78.0.0/16,10.10.40.149/32,10.78.90.32/27,95.54.192.18/32,31.187.97.119/32,10.10.30.0/24
/interface wireless security-profiles remove [find where name=svc-wifi-yastreb]
```

Binary restore option:

`/home/admin-al/assistant/notes/projects/global-network/backups/2026-07-21-yastreb-service-wifi-prechange/yastreb-pre-service-wifi.backup`
