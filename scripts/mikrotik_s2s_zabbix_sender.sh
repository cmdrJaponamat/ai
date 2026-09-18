#!/usr/bin/env bash
# Sends one S2S snapshot to a Zabbix LLD rule and the matching trapper items.
# The only RouterOS access is the read-only SSH call in mikrotik_s2s_status.sh.
set -euo pipefail

readonly ZABBIX_SERVER="127.0.0.1"
readonly ZABBIX_HOST="Mikrotik-ROUTER-AL-OBIT"
readonly ROUTER_HOST="10.78.3.254"
readonly ROUTER_USER="zabbix"
readonly SSH_KEY="/var/lib/zabbix/.ssh/id_ed25519_obit_s2s"
readonly KNOWN_HOSTS="/var/lib/zabbix/.ssh/known_hosts_obit_s2s"
readonly SCRIPT="/usr/lib/zabbix/externalscripts/mikrotik_s2s_status.sh"

snapshot="$(sudo -u zabbix "$SCRIPT" "$ROUTER_HOST" "$ROUTER_USER" "$SSH_KEY" "$KNOWN_HOSTS" 180)"

payload="$(mktemp)"
trap 'rm -f "$payload"' EXIT

python3 - "$snapshot" "$ZABBIX_HOST" >"$payload" <<'PY'
import json
import sys

snapshot = json.loads(sys.argv[1])
host = sys.argv[2]

for entry in snapshot["data"]:
    name = entry["{#S2S.NAME}"]
    # These macro fields become LLD identities, while regular fields are metrics.
    for field, key in (
        ("state", "state"),
        ("handshake_age", "handshake_age"),
        ("rx_bytes", "rx_bps"),
        ("tx_bytes", "tx_bps"),
        ("rx_error", "errors_pps"),
        ("rx_drop", "drops_pps"),
    ):
        value = entry[field]
        if field == "handshake_age" and value < 0:
            value = 0
        print(f"{host}\ts2s.auto.{key}[{name}]\t{value}")

print(f"{host}\ts2s.discovery\t{json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))}")
PY

/usr/bin/zabbix_sender -z "$ZABBIX_SERVER" -T -i "$payload" >/dev/null
