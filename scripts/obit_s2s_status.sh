#!/usr/bin/env bash
# Zabbix external check: current state of all configured S2S transports on AL-OBIT.
# The script uses a dedicated RouterOS account with read-only permissions and an SSH key.
set -euo pipefail

readonly ROUTER_HOST="10.78.3.254"
readonly SSH_KEY="/var/lib/zabbix/.ssh/id_ed25519_obit_s2s"
readonly KNOWN_HOSTS="/var/lib/zabbix/.ssh/known_hosts_obit_s2s"
readonly MAX_HANDSHAKE_AGE=180

# The peer and the transport interface have the same name in the approved site
# configuration.  Counters are read from that interface in the same SSH call;
# this keeps channel state and traffic from being sampled at different moments.
routeros_command=':foreach i in=[/interface/wireguard/peers/find] do={:local n [/interface/wireguard/peers/get $i name]; :local d [/interface/wireguard/peers/get $i disabled]; :local h [/interface/wireguard/peers/get $i last-handshake]; :local f [/interface/find where name=$n]; :if ([:len $f] > 0) do={:put ("WG|" . $n . "|" . $d . "|" . $h . "|" . [/interface/get $f rx-byte] . "|" . [/interface/get $f tx-byte] . "|" . [/interface/get $f rx-drop] . "|" . [/interface/get $f tx-drop] . "|" . [/interface/get $f rx-error] . "|" . [/interface/get $f tx-error])}}; :foreach i in=[/interface/find where type="ovpn-in"] do={:local n [/interface/get $i name]; :local r [/interface/get $i running]; :local d [/interface/get $i disabled]; :put ("OVPN|" . $n . "|" . $d . "|" . $r . "|" . [/interface/get $i rx-byte] . "|" . [/interface/get $i tx-byte] . "|" . [/interface/get $i rx-drop] . "|" . [/interface/get $i tx-drop] . "|" . [/interface/get $i rx-error] . "|" . [/interface/get $i tx-error])}'

raw="$(timeout 20s /usr/bin/ssh \
  -i "$SSH_KEY" \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$KNOWN_HOSTS" \
  "zabbix@${ROUTER_HOST}" "$routeros_command")"

/usr/bin/env S2S_RAW="$raw" /usr/bin/python3 - "$MAX_HANDSHAKE_AGE" <<'PY'
import json
import os
import re
import sys

max_age = int(sys.argv[1])
entries = []

for raw_line in os.environ["S2S_RAW"].splitlines():
    line = raw_line.strip()
    if not line:
        continue
    fields = line.split("|")
    if len(fields) != 10:
        continue
    transport, name, disabled, value, rx_bytes, tx_bytes, rx_drop, tx_drop, rx_error, tx_error = fields
    disabled = disabled.lower() == "true"
    state = 2 if disabled else 0  # 0 down, 1 up, 2 administratively disabled
    age = -1

    if transport == "WG" and not disabled:
        match = re.fullmatch(r"(?:(\d+)d)?(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2})", value)
        if match:
            days, hours, minutes, seconds = (int(item or 0) for item in match.groups())
            age = days * 86400 + hours * 3600 + minutes * 60 + seconds
            state = 1 if age <= max_age else 0
    elif transport == "OVPN" and not disabled:
        state = 1 if value.lower() == "true" else 0

    entries.append({
        "{#S2S.TYPE}": transport,
        "{#S2S.NAME}": name,
        "{#S2S.ENABLED}": 1 if not disabled else 0,
        "state": state,
        "handshake_age": age,
        "rx_bytes": int(rx_bytes),
        "tx_bytes": int(tx_bytes),
        "rx_drop": int(rx_drop),
        "tx_drop": int(tx_drop),
        "rx_error": int(rx_error),
        "tx_error": int(tx_error),
    })

if not entries:
    raise SystemExit("AL-OBIT returned no S2S tunnel records")

print(json.dumps({"data": entries}, ensure_ascii=False, separators=(",", ":")))
PY
