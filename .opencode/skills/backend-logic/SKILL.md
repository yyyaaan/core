---
name: backend-logic
description: Python and Rust coding conventions for the core monorepo — FastAPI, Playwright, uv workspace, Cargo workspace
---

## Python Stack

- Runtime: Python ≥3.14, managed by `uv` workspace
- Web: FastAPI + Uvicorn, Jinja2 templates
- Scraping: Playwright (Chromium, server-side) — this is backend, not frontend
- Data: Pandas, Plotly, OpenCV (headless)
- Browser agent: `browser-use` library with multi-LLM backends
- CLI: argparse for batch scripts

## FastAPI Patterns

- All route handlers are `async def`
- Response types: `HTMLResponse`, `Response(media_type=...)`, plain dict → JSON
- Templates loaded from `templates/` via Jinja2Templates
- No auth in app code — OAuth2-Proxy handles it at ingress level
- Health endpoint: `GET /api/health`

## Playwright Conventions

- Wrap in async context manager (`__aenter__` / `__aexit__`)
- Chromium with custom viewport (1680×1080) and iPad user-agent
- Default timeout 30s, wait for `domcontentloaded`
- Per-element try/except — never fail an entire page on one missing selector
- CSS selectors, not XPath

## Code Style

- No static type checker enforced (no mypy/pyright)
- Minimal type hints — add only where they clarify intent
- Class-level constants for config (cache paths, URLs)
- Private helpers prefixed with `__` (name-mangled) or `_`
- Secrets from env vars (`os.getenv`), never hardcoded
- File-based JSON caching with force-update flags

## Project Layout

```
apps/py-*/
├── pyproject.toml     # app metadata + deps
├── Dockerfile
├── Taskfile.yaml
├── helm-chart/        # per-app deployment
├── src/<pkg>/         # source package
│   ├── main.py        # entry point
│   └── ...
└── tests/             # pytest (framework ready)

packages/py-*/
├── pyproject.toml
└── src/<pkg>/
```

## Rust Stack

- Edition 2021, Cargo workspace with shared deps
- Key crates: tokio (async), serde (serialization), anyhow (errors)
- Workspace deps defined in root `Cargo.toml`, members use `workspace = true`

## Running

| Command | What |
|---------|------|
| `uv run play` | Run py-play locally |
| `uv run autobrowser` | Run autobrowser |
| `cargo run -p rs-y-one` | Run Rust project |
| `task build-all-images` | Build all Docker images |
