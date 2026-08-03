# Cleanup of the admin-vpn diagnostic profile

## Situation

During diagnosis of the NetworkManager profile `admin-vpn`, a separate temporary profile
`admin-vpn-safe-test` was created. The test was not a fix. The user later restored their
FlClashX setup and established a separate, manually started VPN tunnel for administrative work.

## Exact cleanup completed

- Removed the inactive NetworkManager connection `admin-vpn-safe-test`.
- Restored `admin-vpn` to `comp-lzo=no-by-default`.
- Did not alter the active manually started tunnel, FlClashX, Wi-Fi routes, DNS, router rules,
  or VPN-server configuration during cleanup.

## Verification

- Active `tun0` stayed externally managed and connected.
- Default route stayed through the Wi-Fi gateway.
- HTTPS connectivity succeeded.
- `admin-vpn` remained disconnected.

## Follow-up constraint

Do not modify FlClashX or the active manual VPN as part of future `admin-vpn` diagnosis.
Any further live test of `admin-vpn` must be conducted only in an agreed maintenance window
when the active administrative tunnel is not needed.

## Rollback

No rollback is needed. Recreating a test profile is a new, explicitly approved action.
