# packages/py-scout (browser-backed scraping)

CLI, not deployed (no Helm chart). Runs against the user's own Chrome on the Mac, started with `--remote-debugging-port=9222` and the `~/Lab/z-debug-profile` profile (see README). It can't run on the cluster: the targets are behind bot management that blocks non-browser clients, and headless Chrome on the Pi would be flagged too.

## Rules

- Get data from inside a real tab by reusing the page's own API client (e.g. its Apollo client). Don't rebuild requests by hand, don't spoof headers or TLS fingerprints, and don't probe which headers a server actually checks.
- Be polite: sequential requests, randomised delay (`SCOUT_DELAY_*`), stop the whole scan on the first failed request (403, challenge, network error). It's the user's real profile.
- Never `browser.close()` the CDP connection's browser or close tabs scout didn't open; leaving the `connect()` block just disconnects.
- Parsers are pure functions over the JSON the page returns, tested against trimmed real responses in `tests/fixtures/`. Catch per element so one odd row doesn't drop a date.
- Store everything a request returns (all rooms × rates), filter at report time.

## Layout (`src/scout/`)

- `cdp.py`: endpoint resolution (`host.docker.internal` → IP, because Chrome rejects non-IP `Host` headers), `connect()`, `ScoutError`.
- `store.py`: SQLite helper; db at `packages/py-scout/data/` (gitignored, `SCOUT_DB_PATH`).
- `sites/<site>.py`: one module per site. `cli.py`: `scout <site> <action>`.

## Marriott notes

- Rate list page `/reservation/rateListMenu.mi` (Next.js + Apollo, `window.__APOLLO_CLIENT__`). Query `PhoenixBookDTTSearchProductsByProperty`, variables `search.propertyId` (MARSHA code, e.g. `BOBWI`), `search.options.startDate/endDate/numberInParty`. One call returns every room × rate (~100 rows) for one stay. `totalPricing.rateModes.grandTotal` is the "with taxes and fees" price shown on the page.
- Requests are safelisted and signed (`graphql-operation-signature`, tied to the site build), which is why scout runs the page's registered query with its own context instead of storing the query text.
- The page renders the session's last search, so opening the bare URL in the same profile works once any search has been made. URL-param deep links (`/reservation/availability.mi?...`) no longer land on rates.
- Booking window is ~351 days of check-out; packages (e.g. Half Board) and prepay rates open a few days later than standard rates. Dates beyond the window return status error `UER30003 Invalid End Date` (not a GraphQL error).
- The API repeats some room/rate rows; dedupe on (room, rate code, total).
- Low-rate calendar `/search/availabilityCalendar.mi?isRateCalendar=true&isSearch=true&propertyCode=BOBWI`: query `phoenixShopADFSearchProductsByProperty` (separate `phoenix_shop` client), variables `search.options.startDate/endDate/numberOfDays/numberInParty`, `rateRequestTypes: STANDARD`. One call covers ~4 weeks of check-in dates, returned as runs (`startDate`..`endDate` share a price). `lowestAverageRate` is the cheapest standard nightly rate of any room, before taxes; the page adds the destination fee (11,990 XPF/night at BOBWI). Its `totalRate` is not nights × average, so don't rely on it. Not implemented in scout yet.
