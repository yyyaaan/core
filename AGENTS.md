# AGENTS.md

Personal monorepo (private project): Python + Rust services and the Helm/ArgoCD infrastructure for a home k3s cluster on a Raspberry Pi. This file is the vendor-neutral source of truth for coding agents; `CLAUDE.md` only imports it. Nested `AGENTS.md` files add domain rules and win over this one for their subtree.

## Layout

| Path | What |
|------|------|
| `apps/py-play/` | FastAPI app: daily digest email (football, S-Bonus, Migri processing time), spot price chart, water meter camera crop. Browser-free scraping (httpx). Own Helm chart, `web` ns. See `apps/py-play/AGENTS.md` |
| `apps/py-web/` | FastAPI + Jinja2 + HTMX personal site. Zero-Node. See `apps/py-web/AGENTS.md` |
| `apps/bash-poller/` | CronJob workloads (Elenia energy, FFmpeg/timelapse), shell + Python helpers |
| `packages/py-scout/` | CLI price scans through the user's own Chrome over CDP (Marriott first). Not deployed. See `packages/py-scout/AGENTS.md` |
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
uv run scout marriott report --from 2027-10-01 --to 2027-10-31   # needs debug Chrome only for `scan`
cargo build -p rs-y-one && cargo test
helm lint <chart> && helm template t <chart> > /dev/null   # what CI checks
```

py-play routes need an oauth2-proxy email header. Locally: `ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play-dev`.

## How changes ship

- PR → CI (`test-play`, `test-web`: ruff + pytest, results as one PR comment per app updated in place by `.github/scripts/test_comment.py`; `test-poller`: ruff, shellcheck, inline init script compiles; `lint-helm` on any YAML).
- Merge to `main` → `build-<app>.yml` (thin caller of the reusable `_image.yml`) builds the arm64 image to `ghcr.io/yyyaaan/core/<app>` and, in the same run, opens a PR bumping the image tag in the app's values → ArgoCD (watching `main`, manual sync) deploys. If a bump is missing, re-run or manually dispatch the build on `main`; it bumps too.
- So `main` is production. Never run `helm upgrade`/`install` or `kubectl apply` as a way to deploy; propose a change instead.

## Gotchas

- The tag bump uses yq only to locate the line of each path in the `values:` input of `build-<app>.yml` (e.g. `.image.tag`, poller `.imageConfig.tag`), then rewrites just that line's value with sed (yq itself would reflow the file) and fails if anything else changed. Moving the tag key or adding a values file means updating that list; keep trailing comments off the tag line.
- Image tags in app values are bot-managed (`sha-xxxxxxx`); don't hand-edit them.
- Images are built for `linux/arm64` (Pi). Don't add amd64-only dependencies.
- Secrets live in `infra/credentials/*.env` (gitignored) and reach the cluster only via `task infra:secrets` on the host. Never inline secret values in code, values or manifests.
- `apps/py-play` does its own auth check (`play/auth.py`, allowlist on `X-Auth-Request-Email` only, the header Traefik overwrites from oauth2-proxy) on top of oauth2-proxy; `apps/py-web` has none.

## Python conventions

- FastAPI handlers are `async def`; Jinja2 templates under `src/<pkg>/templates/`.
- Config via `pydantic-settings` / env vars, never hardcoded secrets or domains.
- Light type hints, no type checker enforced. Ruff is the formatter and linter.
- Scraping: prefer a site's JSON API or server-rendered HTML over httpx; a browser is the last resort, and then only the user's own Chrome via `packages/py-scout` (never headless or server-side). Catch per element so one missing field doesn't fail a whole page.

## Agent config layout

- Repo skills: `.agents/skills/<name>/SKILL.md` (Codex reads it natively; `.claude/skills` symlinks to it).
- Claude subagents: `.agents/claude/agents/` (`.claude/agents` symlinks to it).
- Nested instructions: put `AGENTS.md` in the subtree and a one-line `CLAUDE.md` containing `@AGENTS.md` beside it, so both Codex and Claude Code pick it up.
- Personal, cross-project instructions live in the user-level `~/.agents/AGENTS.md`, not here.
