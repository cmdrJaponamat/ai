# Battle.net cache reset in PortProton prefix — 2026-10-02

## What changed

With Battle.net and WoW confirmed stopped, the Battle.net agent cache directory was moved, not deleted:

- previous location: `/home/admin-al/PortProton/data/prefixes/BATTLE_NET/drive_c/ProgramData/Battle.net`
- backup: `/home/admin-al/PortProton/data/prefixes/BATTLE_NET/cache-backups/ProgramData-Battle.net-20261002T155355+0300`

The installed game directory `/home/admin-al/PortProton/data/prefixes/BATTLE_NET/drive_c/Program Files (x86)/World of Warcraft` was not modified.

## Why

Blizzard Support requested a Battle.net cache reset after the account showed no expected characters/world list. The prior update failure was `5007 / BLZBNTAGT0000138F`, with the agent logging an empty response from `level3.blizzard.com`.

## Rollback

Do not start Battle.net before rollback. Move the backed-up directory back to its previous location:

```bash
mv -- /home/admin-al/PortProton/data/prefixes/BATTLE_NET/cache-backups/ProgramData-Battle.net-20261002T155355+0300 \
  /home/admin-al/PortProton/data/prefixes/BATTLE_NET/drive_c/ProgramData/Battle.net
```

If a newly created `ProgramData/Battle.net` directory exists, preserve it separately before restoring the backup.
