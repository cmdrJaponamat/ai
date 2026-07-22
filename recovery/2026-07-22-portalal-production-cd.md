# PortalAL production CD

## Problem statement

The PortalAL production host `spb-wiki` (`10.78.3.149`) is in a private
network, so GitHub-hosted runners cannot deploy to it. Deployment had been a
manual server-side operation without a repeatable health-check or rollback.

## Changes made

- Installed GitHub Actions Runner `2.336.0` in `/opt/actions-runner` as user
  `a.kuznetsov`.
- Registered it to `cmdrJaponamat/PortalAL` with label `portal-production`.
- Installed and enabled systemd service:
  `actions.runner.cmdrJaponamat-PortalAL.portal-production.service`.
- Added PortalAL workflow `.github/workflows/deploy-production.yml`:
  pushes to `main` build `portal-al:<commit-SHA>` locally on the runner, update
  the Compose definition, then run `deploy/deploy-image.sh`.
- `deploy/deploy-image.sh` waits for `http://127.0.0.1:5180/api/health`; when
  the new container fails it restores the previous image automatically.
- Production Compose honours `PORTAL_IMAGE`; runtime `.env`, Kerberos keytab,
  `data/`, and `logs/` are not overwritten by CI/CD.

## Verification

- Runner service is `active` and connected to GitHub.
- First successful deploy completed at 2026-07-22 10:51 MSK.
- Portal container image:
  `portal-al:71c2c3148036af7ac9aecfb83600344add0bacdf`.
- Container status is `running (healthy)`.
- `curl http://127.0.0.1:5180/api/health` returns JSON with `ok: true`.

## Follow-up: brandbook 2026 themes

- Deploy `9bf437b618bb0823c8303df6cb766a9f20e98648` added an accessible
  light/dark switcher to the portal header. The selection is stored per browser
  in `localStorage`; the portal admin can set the default for new browsers.
- The approved 2026 palette is `#002FFF` (primary), `#B1D1F5` (secondary), and
  `#D4D3D5` (metal). The outdated green accent was removed from themed UI.
- The production container is healthy after this deploy and its built JS contains
  the `themeToggle` control.
- Exact `Graphik LCG` web-font files were not present in the supplied brandbook
  directory; obtain licensed `.ttf/.otf` files before final typography alignment.

## Follow-up: contrast and icon correction

- Deploy `8ccb26b3bfc53db890b734011f69ac579aac2fd2` uses the approved horizontal
  monochrome PDF converted directly to SVG for the dark header, then renders it
  white. This avoids the quality loss from the temporary 172-pixel PNG.
- The dark-home heading explicitly uses the light theme token, fixing its black
  text on a dark panel. Favicon, Apple Touch Icon and PWA icons are regenerated
  from the approved 2026 vertical mark; PWA metadata uses `#002FFF` and
  `#F7F8FC`.
- Deploy `250edda4baec4350d6f36474bdb2854cd40fc09f` adds transparent monochrome
  browser favicon assets. The document selects black for light browser chrome
  and white for dark browser chrome through `prefers-color-scheme`; a transparent
  black ICO remains as a legacy fallback.
- Deploy `a821b647f5a289c2cc1e6961b05013a13898a6f1` places the monochrome mark
  inside a 128-pixel transparent canvas with a 92-pixel safe area, preventing
  clipping in narrow browser tabs.
- Deploy `017267b93af987d699d4ca28e78fe4c95e103452` uses a transparent vector
  four-point variant for the browser favicon. It is selected black/white using
  `prefers-color-scheme` and is intended for legibility at 16×16 pixels.
- Deploy `06e9c3aa9bce3aad7de112f3ae268f32c1f268b6` supersedes the experimental
  variant with the approved black-and-white vertical mark from the brandbook's
  vector PDF. The favicon assets crop only the mark viewport; no custom graphic
  element is present.
- Deploy `8f9ae1acd02864e6201c463052f88999a280e742` applies `color: var(--ink)`
  at the application root. This fixes inherited black text across dark cards,
  section titles and page headers while preserving component-specific colors.
- Deploy `ec2580bcbceaa290fbacb6b336feb4ae0dc2da94` references
  `favicon-brandbook-light.svg` and `favicon-brandbook-dark.svg` instead of
  reused favicon URLs, forcing clients to fetch the approved vector artwork.
- Deploy `fcd7d72fe6abaa79e82b3d117156700d8744d417` switches the dark login
  screen to the approved monochrome horizontal vector logo. Its brand panel uses
  a blue-to-graphite gradient and no longer renders the former green accent mark.
- Deploy `45705ea4a40319d23f54bf14b6eb9d2cc3867b30` applies the same branded
  logo panel in the light theme, removing the remaining pale decorative login
  panel and white-background logo treatment.
- Deploy `975f03645afe3159aee2e6b7d03146a98c97883d` returns `authMode` and a
  null user from `/api/auth/logout`; the frontend resets its page state and
  renders the SSO authorization screen immediately after logout.

## Follow-up: administrative services

- Deploy `2ea0f900448accd9d68de9dad1706d4f80e0a83f` adds the following
  admin-only catalog links:
  - Oxidized production: `http://10.78.3.70:8888/prod/nodes`
  - KSMG: `https://10.78.3.155/ru_RU/#/rules`
  - Kaspersky Security Center: `https://ksc.aurora-logistics.ru:8080/`
  - Zabbix: `https://zabbix.aurora-logistics.ru/`
- Production static-catalog readback confirms all four entries have
  `visibleFor: ["admin"]`.
- The portal uses a persisted PostgreSQL `content-store` overlay. On the first
  deploy, its baseline/catalog predated the new JSON and hid the entries. The
  four missing IDs were appended to both branches without resetting any other
  managed-content changes; a repository readback for role `admin` confirms all
  four are now returned to the UI.

## Follow-up: IT Wiki links

- Deploy `3e633e98d46c6c04cbec3353d777f52450fed2a3` updates the protected
  portal section «ИТ: база знаний» to the canonical `/ru/it` Wiki route and
  expands it to 28 cards. New cards include the equipment registry, data
  center and network equipment, corporate gateways, workplaces, print, VKS,
  specialised equipment, four documented site networks and the WAN registry.
- `scripts/seed-it-knowledge.mjs` preserves manual titles, descriptions and
  other card fields: it updates only canonical Wiki URLs for known cards and
  appends missing IT cards. The deploy script now runs this seed after a
  successful health-check. The runtime image includes the generated bootstrap
  catalog required by the seed.
- Verified directly in the production managed store: 28 IT cards and the
  `/ru/it` section URL are present; equipment, gateway, Milionnaya and WAN
  links resolve to their intended Wiki paths.

## Follow-up: administrative service groups

- Deploy `3193a705700b7295f20e0b607e9781d2c8b7ee44` groups cards after
  search/filtering into network/access, compute/storage, information security,
  monitoring and other administrative systems. Empty groups are not rendered.
- Deploy `220fadf58ce70cafdf7ad5a8cff32c7e256c31ca` defines fixed card-preview
  slots for title, description, technical metadata, owner and actions across
  services, employees, news, offices and departments. Empty slots remain in
  place; preview text is line-clamped so card levels stay aligned.

## Rollback

For one portal release, in `/opt/portal-al` select the previous local image and
recreate only the portal container:

```bash
export PORTAL_IMAGE=portal-al:<previous-sha-or-portal-al:local>
docker compose up -d --no-build portal
curl -fsS http://127.0.0.1:5180/api/health
```

To stop CD while keeping the portal running:

```bash
sudo systemctl disable --now actions.runner.cmdrJaponamat-PortalAL.portal-production.service
```

To unregister/remove the runner, first obtain a GitHub runner removal token,
then run `/opt/actions-runner/config.sh remove --token <token>` and remove the
runner directory only after confirming no jobs are active.

## Restart/reboot

No relogin or reboot is required. The runner is enabled at boot; each deploy
recreates only the `portal` Docker container.
