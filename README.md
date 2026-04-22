# YYYaan Core Monorepo

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Cluster-326CE5?logo=kubernetes&logoColor=white)
![Argo CD](https://img.shields.io/badge/ArgoCD-GitOps-EF7B4D?logo=argo&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?logo=githubactions&logoColor=white)

## Overview 🧭

Monorepo for Python and Rust services with a GitOps-first deployment model.

- Monorepo structure for apps, packages, and crates
- Python services (FastAPI), REST APIs, and MCP-related tooling
- Kubernetes + Helm for runtime infrastructure
- Argo CD for in-cluster deployment and reconciliation

Manual `helm apply` is intentionally avoided. Deployments are managed through Argo CD and currently require manual approval in addition to pull requests.

Home automation components (Home Assistant, Homebridge, Frigate, etc.) are maintained under `infra/helm-chart` as part of core infrastructure.

## CI/CD ⚙️

- GitHub Actions: build, test, lint, and image workflows
- In-cluster Argo CD: Helm/Kubernetes deployment execution

## Technologies

- Kubernetes, Helm, networking, oauth2-proxy
- Python, FastAPI, uv, pytest, ruff
- GitHub Actions and go-task (`Taskfile`)
- Cloudflare tunnel for public ingress (in-cluster)

`Taskfile` manages local and cloud workflows. See [taskfile.dev](https://taskfile.dev) and [go-task/task](https://github.com/go-task/task).

## Repository Layout

- `apps/`: main applications
- `packages/`: shared Python packages
- `crates/`: Rust crates

Naming convention:
- `py-*` for Python projects
- `rs-*` for Rust projects

## Quick Start (Dev) 🚀

Use the devcontainer for Python and Rust development. Infrastructure flows are GitOps-based and should be validated from host/cluster context.

```bash
uv run autobrowser
uv run play

# Unit tests (workspace)
uv run pytest -v

# Local auth example for play
ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play
```

## Services 🏠

- Home internal: Home Assistant, MariaDB, Homebridge, Frigate
- General web: Play (FastAPI), Stirling PDF (on-demand)
- Supporting: OAuth2 Proxy, Headlamp, Cloudflare tunnel, cert issuers

## Restic Backups 💾

A Kubernetes CronJob backs up MariaDB and configuration folders.

## Kubernetes Context Reminder

```bash
export KUBECONFIG=~/.kube/pi-config
```

Default kube context is `config` if not overridden.