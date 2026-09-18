#!/usr/bin/env bash
# Send real UDP/53 DNS probes from the Zabbix server to local trapper items.
set -euo pipefail

readonly SERVER='127.0.0.1'
readonly ZABBIX_HOST='Mikrotik-ROUTER-AL-OBIT'
readonly PROBE='/usr/lib/zabbix/externalscripts/dns_udp_probe.sh'

probe() {
  "$PROBE" "$1" "$2" "$3" 2>/dev/null || printf '0\n'
}

send() {
  /usr/bin/zabbix_sender -z "$SERVER" -s "$ZABBIX_HOST" -k "$1" -o "$2" >/dev/null
}

send dns.unbound.external.availability "$(probe 10.78.4.253 google.com availability)"
send dns.unbound.external.latency "$(probe 10.78.4.253 google.com latency)"
send dns.unbound.corp.availability "$(probe 10.78.4.253 aurora-logistics.local availability)"
send dns.cloudflare.availability "$(probe 1.1.1.1 google.com availability)"
send dns.cloudflare.latency "$(probe 1.1.1.1 google.com latency)"
send dns.google.availability "$(probe 8.8.8.8 google.com availability)"
send dns.google.latency "$(probe 8.8.8.8 google.com latency)"
send dns.yandex.availability "$(probe 77.88.8.8 google.com availability)"
send dns.yandex.latency "$(probe 77.88.8.8 google.com latency)"
