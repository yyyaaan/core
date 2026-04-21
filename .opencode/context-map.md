# Context Map — Core Monorepo

> Sisyphus: read this before every delegation.

## Workspace Layout

| Path | Type | Purpose |
|------|------|---------|
| `apps/py-play/` | Python (FastAPI) | Web app — Playwright scraping, OpenCV, data viz |
| `apps/py-web/` | Python (FastAPI) | Web app scaffold — FastAPI, Jinja2 templates, multipart forms |
| `apps/bash-poller/` | Shell/Python | CronJobs — Elenia energy, FFmpeg, timelapse |
| `packages/py-autobrowser/` | Python | Agentic browser automation via `browser-use` |
| `crates/rs-y-one/` | Rust | Rust learning project |
| `infra/helm-chart/` | Helm | K8s services: HA, Frigate, MQTT, MariaDB, OAuth2 |
| `infra/gitops-config/` | YAML | ArgoCD app-of-apps definitions |
| `infra/bootstrap/` | YAML/Shell | Cluster bootstrap, certs, RBAC, tunnels |
| `infra/credentials/` | env files | Secrets (never commit values, templates only) |

## Tooling

- **Task runner**: `go-task` (Taskfile.yaml at each level)
- **Python**: `uv` workspace, Python 3.14.x only
- **Rust**: Cargo workspace, edition 2021
- **Deploy**: ArgoCD GitOps on k3s (Raspberry Pi)
- **Networking**: Cloudflare tunnel → Traefik → services

## Delegation Rules

### By domain

| Task domain | Delegate to | Skill to load |
|-------------|-------------|---------------|
| Architecture / planning | **Prometheus** | `monorepo-arch` |
| Python / Rust / backend code | **Hephaestus** | `backend-logic` |
| Helm / K8s / GitOps | **Hephaestus** | `infra-helm` |
| Code search / file lookup | **Librarian** | — |

### By app

| App path | Stack | Notes |
|----------|-------|-------|
| `apps/py-play/` | FastAPI, Jinja2, Playwright, OpenCV, Pandas, Plotly | Web scraper + data viz. Has own helm-chart, deploys to `web` ns |
| `apps/py-web/` | FastAPI, Jinja2, python-multipart, Uvicorn | New web app scaffold under `src/web` with tests in `tests/` |
| `apps/bash-poller/` | Shell, Python helpers | CronJob workloads (Elenia, FFmpeg, timelapse). Deploys to `home-internal` ns |
| `packages/py-autobrowser/` | browser-use, Pydantic Settings, multi-LLM | Agentic browser automation. Library, not deployed standalone |
| `crates/rs-y-one/` | Tokio, Serde, Anyhow | Rust learning project |
| `infra/helm-chart/` | Helm, Traefik, cert-manager | Platform services chart. See `infra-helm` skill |

Playwright and browser-use are **backend** tools in this repo — they run server-side, not in a browser frontend.

## Critical Constraints

- Credentials live in `infra/credentials/*.env` — never inline secrets
- Helm values split: `values.yaml` (prod) and `values-test.yaml` (test domain)
- All Python apps share root `pyproject.toml` via `uv` workspace members
- Rust crates share root `Cargo.toml` workspace dependencies
