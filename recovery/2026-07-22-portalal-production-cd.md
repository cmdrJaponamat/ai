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
