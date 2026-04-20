---
name: monorepo-arch
description: Architecture reference for the core monorepo — workspace layout, dependency graph, build and deploy patterns
---

## Structure

```
core/
├── apps/           # Deployable applications (each has own helm-chart/)
│   ├── py-play/    # FastAPI web app (Playwright, OpenCV, Plotly, Pandas)
│   └── bash-poller/# CronJob workloads (Elenia, FFmpeg, timelapse)
├── packages/       # Shared Python libraries
│   └── py-autobrowser/  # browser-use agentic automation
├── crates/         # Rust workspace members
│   └── rs-y-one/   # Rust learning project
└── infra/          # Infrastructure-as-code
    ├── helm-chart/ # Main infra chart (HA, Frigate, MQTT, MariaDB, OAuth2, PDF)
    ├── gitops-config/  # ArgoCD app-of-apps
    ├── bootstrap/  # Cluster init (certs, RBAC, tunnels)
    └── credentials/# Secret templates (*.env)
```

## Dependency Graph

- `uv` workspace: root `pyproject.toml` → `apps/py-*`, `packages/py-*`
- Cargo workspace: root `Cargo.toml` → `crates/rs-*`
- Helm charts are standalone per app; infra chart covers all platform services

## Build & Deploy

| Action | Command |
|--------|---------|
| Run play locally | `uv run play` |
| Run autobrowser | `uv run autobrowser` |
| Build all images | `task build-all-images` |
| Lint helm charts | `task lint-helm` |
| Bootstrap cluster | `task bootstrap` |
| Deploy py-play | `task deploy-play` |

## Deploy Target

- **Platform**: k3s on Raspberry Pi
- **GitOps**: ArgoCD watches this repo, auto-syncs helm releases
- **Ingress**: Cloudflare tunnel → Traefik → per-service ingress
- **Auth**: OAuth2-Proxy in front of protected routes
- **Storage**: hostPath + local-path provisioner; MariaDB for HA
- **Backup**: Restic → Backblaze S3 on daily cron

## Conventions

- Python prefix: `py-*` | Rust prefix: `rs-*`
- Each app owns its `helm-chart/` with `Chart.yaml` + `values.yaml`
- Secrets: env-file templates in `infra/credentials/`, sealed in-cluster
- No hardcoded domains — `values.yaml` drives `{{ .Values.domain }}`
