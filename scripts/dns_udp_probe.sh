#!/usr/bin/env bash
# Zabbix external check: verify real DNS resolution via UDP/53.
# Usage: dns_udp_probe.sh <resolver-ip> <fqdn> <availability|latency>
set -euo pipefail

resolver="${1:?resolver IP is required}"
fqdn="${2:?FQDN is required}"
metric="${3:-availability}"

result="$(/usr/bin/dig +notcp +time=2 +tries=1 +stats "@${resolver}" "${fqdn}" A 2>/dev/null || true)"
status="$(awk '/^;; ->>HEADER<<-/{sub(/^.*status: /, ""); sub(/,.*/, ""); print; exit}' <<<"${result}")"
elapsed="$(awk '/^;; Query time:/{print $4; exit}' <<<"${result}")"

case "${metric}" in
  availability)
    # NOERROR proves the resolver returned a usable external/corporate answer.
    [[ "${status}" == "NOERROR" ]] && printf '1\n' || printf '0\n'
    ;;
  latency)
    [[ "${status}" == "NOERROR" && "${elapsed}" =~ ^[0-9]+$ ]] && printf '%s\n' "${elapsed}" || printf '0\n'
    ;;
  *)
    echo "Unknown metric: ${metric}" >&2
    exit 2
    ;;
esac
