---
name: infra-upgrade
description: Upgrade platform service images (Home Assistant, Homebridge, Frigate, MariaDB, Mosquitto, oauth2-proxy, Restic, Stirling-PDF) or bootstrap charts (Traefik, Headlamp) in infra/. Use when asked to bump, update or upgrade infra versions, or to check what's outdated.
---

# Infra upgrade

Goal: a reviewed tag bump plus a short risk report. The edit is trivial; the value is in the release-note review.

## 1. Inventory

- Images: `image.repository` / `image.tag` in `infra/helm-chart/values.yaml`. `values-test.yaml` pins some services separately (often older); report the drift, ask before aligning.
- Bootstrap charts: `targetRevision` in `infra/gitops-config/bootstrap-cluster/apps.yaml`.
- Skip floating `latest` tags (Stirling-PDF, cloudflared) unless asked.

## 2. Pick targets

- Latest stable release from the upstream GitHub releases or registry. No betas/RCs, unless currently on one and moving to its stable.
- Keep each tag's format and variant: HA `YYYY.M.P`, Homebridge date tags, `-alpine` suffixes, MariaDB on its LTS line.
- Confirm the target tag exists for `linux/arm64`.

## 3. Review every release in between

Read release notes for all versions from current to target, not just the last one. Flag:

- Breaking changes and removed/renamed config. HA and Frigate configs live on the Pi's hostPath, not in this repo, so any needed config edit is a manual step for me.
- Frigate: changes to `/api/export/custom/...` or `/api/exports` (used by bash-poller), and to MQTT topics.
- Mosquitto: auth/listener defaults (py-play, HA and Frigate publish to it).
- MariaDB: version line changes and data migrations; HA runs its own schema migration on start.
- oauth2-proxy: renamed or removed flags vs `templates/oauth2-proxy/configmap.yaml`.
- Traefik/Headlamp chart majors: values and CRD changes.

## 4. Edit and verify

- Change only the tags (and test pins if agreed).
- `helm lint infra/helm-chart` and `helm template t infra/helm-chart [-f infra/helm-chart/values-test.yaml] > /dev/null`.

## 5. Report

A table of service, current → target, and risk (none/low/manual step/breaking), then:

- Manual steps on the Pi (config edits, a fresh backup before MariaDB or other stateful upgrades).
- Suggested ArgoCD sync order when it matters (e.g. MariaDB before HA).
- A suggested commit message. Don't commit.
