# Remote Ansible Tree Repacked For Private Git

Date: 2026-04-08
Target host: `10.78.3.10`
Working path: `/opt/ansible/projects`

## Problem

The live Ansible tree needed to be published to a private GitHub repository without splitting it into multiple folders and without leaking secrets, internal inventory, bootstrap passwords, logs, or local runtime files.

## Findings

- The live tree was under `/opt/ansible/projects`.
- Sensitive data existed in:
  - `inventories/production/group_vars/all/vault.yml`
  - `inventories/production/group_vars/all/zabbix.yml`
  - `inventories/production/inventory.ini`
  - `inventories/production/host_vars/spb-logging.yml`
  - `inventories/production/group_vars/all/ClonedVMIP.yml`
  - `ansible-bootstrap/linux_hosts.txt`
  - `logs/ansible.log`
- `a.kuznetsov` initially lacked write access to parts of the tree; group permissions were later fixed and `sudo -n` worked.
- GitHub access from the remote host currently fails with `Permission denied (publickey)`.

## Exact Changes Made

- Initialized git in `/opt/ansible/projects`.
- Added `.gitignore` for:
  - `logs/`
  - `ansible-venv/`
  - `.ansible/`
  - `.cache/`
  - local `inventory.ini`
  - local `vault.yml`
  - local `local.yml`
  - local `ClonedVMIP.yml`
  - host-specific `host_vars/*.yml`
  - `ansible-bootstrap/linux_hosts.txt`
  - local backup directories `.repack-backup-*`
- Repacked tracked data so the repository keeps one working tree but only safe files are tracked:
  - added `inventories/production/inventory.example.ini`
  - added `inventories/production/group_vars/all/vault.example.yml`
  - added `inventories/production/group_vars/all/local.example.yml`
  - added `inventories/production/group_vars/all/ClonedVMIP.example.yml`
  - added `inventories/production/host_vars/spb-logging.example.yml`
  - added `ansible-bootstrap/linux_hosts.example.txt`
- Moved live secret values into ignored local files:
  - `inventories/production/group_vars/all/vault.yml`
  - `inventories/production/group_vars/all/local.yml`
- Replaced hardcoded environment defaults in tracked role files with generic placeholders and variable-based lookups:
  - `roles/pve-clone-vm/defaults/main.yml`
  - `roles/zabbix-agent/defaults/main.yml`
  - `roles/zabbix-host/tasks/main.yml`
  - `roles/system-time/defaults/main.yml`
  - `roles/network-static/templates/ens18.network.j2`
- Removed stale editor swap file `roles/zabbix-host/tasks/.main.yml.swp`.
- Added remote `origin`:
  - `git@github.com:cmdrJaponamat/ansible_al.git`
- Created the first commit:
  - `af84ff0 Prepare ansible tree for private git repo`

## Verification

- `git status --short --ignored` on the remote host showed only safe project files as tracked candidates and confirmed local-only files are ignored.
- Tracked/staged files were scanned for the known leaked tokens, bootstrap password, and internal addressing markers before commit.
- `git log --oneline -1` on the remote host returned commit `af84ff0`.

## Rollback

- On `10.78.3.10`, restore from:
  - `/opt/ansible/projects/.repack-backup-20260408-060735`
- If the git repository itself should be removed:
  - delete `/opt/ansible/projects/.git`
- If needed, restore ignored local files from the same live tree:
  - `inventories/production/group_vars/all/vault.yml`
  - `inventories/production/group_vars/all/local.yml`
  - `inventories/production/inventory.ini`
  - `inventories/production/host_vars/spb-logging.yml`
  - `inventories/production/group_vars/all/ClonedVMIP.yml`
  - `ansible-bootstrap/linux_hosts.txt`

## Relogin/Restart/Reboot

No.

## Next Step

Configure GitHub SSH authentication for `a.kuznetsov` on `10.78.3.10`, then run:

```bash
cd /opt/ansible/projects
git push -u origin master
```
