# Wiki.js IT Links: Locale Prefix Fix

## Problem

Wiki.js uses `it` as the Italian locale code. Published IT pages have internal API paths such as `it/architecture`, but public URLs without a locale prefix (`/it/architecture`) were interpreted as Italian pages and returned HTTP 404.

## Changes

- Updated Markdown links in `/home/admin-al/assistant/notes/projects/inventory-wiki/wiki-content/it/` to use `/ru/it/...`.
- Re-published all 17 IT pages via `publish_it_wiki.py`.
- Updated portal source/generated catalog and added `scripts/migrate-wiki-ru-paths.mjs` in `PortalAL`; deployed commit `e124a49` and ran the migration on the portal host.
- Added backward-compatible redirects on `10.78.3.1` in `/etc/nginx/conf.d/wiki.aurora-logistics.ru.conf`:
  - `/it` -> `/ru/it`
  - `/it/*` -> `/ru/it/*`

## Verification

- `sudo nginx -t` passed and Nginx was reloaded.
- `https://wiki.aurora-logistics.ru/it/architecture` returns 301 to `/ru/it/architecture`, then 200.
- All 16 currently referenced internal IT Markdown links return HTTP 200.

## Rollback

On `10.78.3.1`, restore the latest `/etc/nginx/conf.d/wiki.aurora-logistics.ru.conf.bak-*`, run `sudo nginx -t`, then `sudo systemctl reload nginx`.

## Restart/Reboot

No reboot or relogin required.
