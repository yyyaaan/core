# AGENTS.md

Personal monorepo (private project): Python + Rust services and the Helm/ArgoCD infrastructure for a home k3s cluster on a Raspberry Pi. This file is the vendor-neutral source of truth for coding agents; `CLAUDE.md` only imports it. Nested `AGENTS.md` files add domain rules and win over this one for their subtree.

## Layout

| Path | What |
|------|------|
| `apps/py-play/` | FastAPI app: daily football + S-Bonus digest email, spot price chart, water meter camera crop. Browser-free scraping (httpx). Own Helm chart, `web` ns. See `apps/py-play/AGENTS.md` |
| `apps/py-web/` | FastAPI + Jinja2 + HTMX personal site. Zero-Node. See `apps/py-web/AGENTS.md` |
| `apps/bash-poller/` | CronJob workloads (Elenia energy, FFmpeg/timelapse), shell + Python helpers |
| `packages/py-autobrowser/` | `browser-use` agentic browser library, not deployed on its own |
| `crates/rs-y-one/` | Rust learning project (tokio, serde, anyhow) |
| `infra/` | Platform Helm chart, ArgoCD app-of-apps, cluster bootstrap. See `infra/AGENTS.md` |

Naming: `py-*` for Python, `rs-*` for Rust. Every deployable app owns a `helm-chart/`.

## Environment

Work happens in the devcontainer (`.devcontainer/`). By design it has **no kubectl, no kubeconfig and no Docker**, and `go-task` is not installed either. Don't try to reach the cluster or build images from here; Taskfile targets that call `kubectl`/`docker`/`helm upgrade` are for the host only.

- Python: uv workspace (root `pyproject.toml`), Python `==3.14.*` only. Add deps with `uv add --package <name> <dep>`, never pip. Commit `uv.lock`; CI runs `uv lock --check`.
- Rust: Cargo workspace (root `Cargo.toml`); shared deps in `[workspace.dependencies]`, members use `dep = { workspace = true }`. `CARGO_TARGET_DIR` lives outside the repo.

## Commands (verified in the container)

```bash
uv run pytest -q                                  # all Python tests
uv run pytest apps/py-web/tests/                  # one app
uv run ruff check apps/py-play/ apps/py-web/      # what CI lints
uv run ruff format <paths>
uv run play-dev                                   # py-play locally, port 7999
uv run web                                        # py-web locally, port 8001
cargo build -p rs-y-one && cargo test
helm lint <chart> && helm template t <chart> > /dev/null   # what CI checks
```

py-play routes need an oauth2-proxy email header. Locally: `ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play-dev`.

## How changes ship

- PR → CI (`test-play`, `test-web`: ruff + pytest; `lint-helm` on any YAML).
- Merge to `main` → GitHub Actions builds arm64 images to `ghcr.io/yyyaaan/core/<app>` → a bot opens a PR bumping `tag:` in the app's `values*.yaml` → ArgoCD (watching `main`, manual sync) deploys.
- So `main` is production. Never run `helm upgrade`/`install` or `kubectl apply` as a way to deploy; propose a change instead.

## Gotchas

- The tag-bump workflow `sed`s **every** line matching `tag:` in `apps/*/helm-chart/values*.yaml`. Never add another `tag:` key in those files (name it differently).
- Image tags in app values are bot-managed (`sha-xxxxxxx`); don't hand-edit them.
- Images are built for `linux/arm64` (Pi). Don't add amd64-only dependencies.
- Secrets live in `infra/credentials/*.env` (gitignored) and reach the cluster only via `task infra:secrets` on the host. Never inline secret values in code, values or manifests.
- `apps/py-play` does its own auth check (`play/auth.py`, `X-Forwarded-Email` allowlist) on top of oauth2-proxy; `apps/py-web` has none.

## Python conventions

- FastAPI handlers are `async def`; Jinja2 templates under `src/<pkg>/templates/`.
- Config via `pydantic-settings` / env vars, never hardcoded secrets or domains.
- Light type hints, no type checker enforced. Ruff is the formatter and linter.
- Scraping: prefer a site's JSON API or server-rendered HTML over httpx; a headless browser is the last resort (only `packages/py-autobrowser` uses one, server-side). Catch per element so one missing field doesn't fail a whole page.

## Agent config layout

- Repo skills: `.agents/skills/<name>/SKILL.md` (Codex reads it natively; `.claude/skills` symlinks to it).
- Claude subagents: `.agents/claude/agents/` (`.claude/agents` symlinks to it).
- Nested instructions: put `AGENTS.md` in the subtree and a one-line `CLAUDE.md` containing `@AGENTS.md` beside it, so both Codex and Claude Code pick it up.
- Personal, cross-project instructions live in the user-level `~/.agents/AGENTS.md`, not here.
