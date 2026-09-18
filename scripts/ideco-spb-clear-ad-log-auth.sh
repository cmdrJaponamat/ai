#!/usr/bin/env bash
# Сбрасывает только динамическое AD-log сопоставление одного тестового IP
# на петербургском Ideco. Не изменяет постоянную конфигурацию NGFW.
set -euo pipefail

readonly IDECO_HOST='192.168.203.82'
readonly TEST_SUBNET_PREFIX='10.76.40.'

if [[ $# -ne 1 || ! $1 =~ ^10\.76\.40\.([1-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-4])$ ]]; then
  echo "Использование: $0 ${TEST_SUBNET_PREFIX}<1-254>" >&2
  echo "Разрешены только адреса тестового VLAN 1400 в Санкт-Петербурге." >&2
  exit 64
fi

readonly CLIENT_IP=$1
readonly VAULT='/home/admin-al/ansible_al/inventories/production/group_vars/mikrotik/vault.yml'
readonly PASSWORD
PASSWORD=$(sed -n 's/^mikrotik_access_password: *"\(.*\)"$/\1/p' "$VAULT")

if [[ -z $PASSWORD ]]; then
  echo 'Не удалось получить учётные данные ansible из vault.' >&2
  exit 1
fi

echo "Сбрасываю AD-log сопоставление для ${CLIENT_IP} на Ideco SPB (${IDECO_HOST})."
SSHPASS="$PASSWORD" sshpass -e ssh \
  -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 \
  "ansible@${IDECO_HOST}" "bash -s -- '${CLIENT_IP}'" <<'REMOTE'
set -euo pipefail
client_ip=$1
export ETCDCTL_ENDPOINTS='http://127.0.0.1:2479'
mapping_key="/ad/auths_by_log/v2/records/${client_ip}"
session_key="/auth/sessions/v3/records/auth_session.${client_ip}_32"

echo 'Было сопоставление:'
etcdctl get "$mapping_key" --print-value-only || true
etcdctl del "$mapping_key" >/dev/null

# auth-backend подписан на удаление mapping_key и завершает LOG-сессию.
for _ in {1..10}; do
  if [[ -z $(etcdctl get "$session_key" --print-value-only) ]]; then
    echo "Готово: LOG-сессия ${client_ip} завершена."
    exit 0
  fi
  sleep 1
done

echo "Сопоставление удалено, но сессия ещё видна. Проверьте ideco-auth-backend." >&2
exit 2
REMOTE
