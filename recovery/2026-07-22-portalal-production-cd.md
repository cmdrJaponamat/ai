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
