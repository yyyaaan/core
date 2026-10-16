# apps/py-play (personal utilities)

FastAPI app in the `web` namespace behind oauth2-proxy, plus its own `X-Forwarded-Email` allowlist (`auth.py`) on private routes. No browser: every upstream is fetched with httpx.

## Routes

| Route | What | Consumer |
|-------|------|----------|
| `GET /view` | Today's digest HTML (cached in memory) | Browser |
| `POST /scheduled?audience=N` | Rebuild digest, email first N of `email_recipients` (0 = refresh only) | `play-mailing` CronJob, 09:39 Europe/Helsinki |
| `GET /public/spot` | Nordpool FI 15-min spot price chart (Plotly, plotly.js inlined) | Home Assistant |
| `GET /public/water.jpg` | Water meter crop of Frigate's `tech` camera | Home Assistant |

`/public/*` paths are configured in HA by hand (see `infra/README.md`); don't rename them. Upstream `httpx` failures map to 502.

## Layout (`src/play/`)

- `config.py`: all settings (`pydantic-settings`, env vars). `TZ` comes from the `tz-config` secret, `SMTP2GO_API_KEY` from `email-credentials`.
- `digest/`: `bbc.py` (fixtures), `hok.py` (Bonus tuplana), `build.py` (assemble + cache), rendered with `templates/digest.html` (email-safe inline styles).
- `energy/`: `spot.py` (Elering prices + chart, cached per quarter-hour), `water.py` (Pillow crop).
- `mail.py`: SMTP2GO MIME endpoint. `httpclient.py`: shared `httpx.AsyncClient` factory.

## Upstreams

- BBC: JSON API `web-cdn.api.bbci.co.uk/wc-poll-data/container/sport-data-scores-fixtures` (what the scores page itself calls). Times are UTC ISO; convert with `zoneinfo`.
- HOK-Elanto: Next.js server-rendered page. Campaigns are `<li>` items (or `- ` lines) inside the `<article>` whose `h2` contains "tuplana"; an empty list means no campaign. The parser raises if that section disappears, so a layout change shows up as "failed to load content" instead of a silent "no offer".
- Elering `api/nps/price`: 15-min resolution since Nordpool's 2025 switch; the `end` bound is inclusive.

## Tests

`uv run pytest apps/py-play/tests/`. Parsers are tested against trimmed real responses in `tests/fixtures/` (HOK ones come from Wayback snapshots covering each format editors have used). When a site changes, add a new fixture instead of editing old ones.
