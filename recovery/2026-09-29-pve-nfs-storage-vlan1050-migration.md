# Proxmox NFS datastore: перенос на Synology storage VLAN1050

**Дата:** 2026-09-29  
**Storage:** `synology-exchange-dag`  
**Назначение:** будущие диски третьего участника Exchange DAG.

## Изменение

DSM NFS export `/volume2/pve-exchange-dag` теперь разрешён только:

- `10.78.5.11` (`spb-pve1`);
- `10.78.5.12` (`spb-pve2`).

Proxmox storage пересоздан штатной командой `pvesm` с тем же ID и export, но
новым endpoint:

```ini
nfs: synology-exchange-dag
    export /volume2/pve-exchange-dag
    path /mnt/pve/synology-exchange-dag
    server 10.78.5.10
    content rootdir,images
    nodes spb-pve2,spb-pve1
    options vers=4.1
    preallocation off
```

PVE3 намеренно исключён: у него нет физического пути в Fabric B/VLAN1050.

`pvesm set` не позволяет изменять фиксированный параметр `server`; поэтому
пустой старый storage был удалён и создан заново. До этого на PVE1 сохранён
`/root/storage.cfg.pre-synology-exchange-dag-vlan1050-20260929`.

## Приёмка

- NFSv4.1 mount с PVE1 и PVE2 до `10.78.5.10` прошёл;
- на каждом выполнены create/sync/remove в mountpoint;
- `synology-exchange-dag` active на PVE1/PVE2, mount source:
  `10.78.5.10:/volume2/pve-exchange-dag`;
- на PVE3 storage disabled;
- `pvesm list` пуст: VM-дисков на datastore нет;
- все 8 production MSA multipath paths сохраняют `active/running/ready`.

## Откат

Откат нужен только до появления VM-дисков. Сначала через DSM вернуть NFS ACL
для прежних `10.78.7.201-203`, затем удалить новый storage и восстановить
`/etc/pve/storage.cfg` из сохранённого PVE1 файла. После этого проверить
mounts на всех трёх PVE. Не возвращать endpoint в VLAN1070 после размещения
VM-дисков без отдельного окна и подтверждения целостности.
