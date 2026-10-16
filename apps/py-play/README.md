# play

Personal utilities on the home cluster: a daily football + S-Bonus digest email, a Nordpool spot price chart and a water meter camera crop for Home Assistant. See `AGENTS.md` for routes and upstreams.

Run locally (port 7999):

- `ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play-dev`
- or `curl -H 'X-Forwarded-Email: yan@yan.fi' http://localhost:7999/view`

Tests: `uv run pytest apps/py-play/tests/`
