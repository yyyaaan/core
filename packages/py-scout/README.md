# py-scout

Price scans for sites that only answer a real browser. scout attaches to your own Chrome over CDP (Playwright `connect_over_cdp`, no bundled browsers) and asks the page's own API client for the data, so requests carry your real cookies and the site's own headers.

## Start Chrome (on the Mac)

Quit Chrome first (Cmd+Q), otherwise this only opens a window in the running instance:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=$HOME/Lab/z-debug-profile \
  --no-first-run
```

Check: `http://localhost:9222/json/version` on the Mac. From the devcontainer scout resolves `host.docker.internal` to an IP itself (Chrome rejects hostnames in the `Host` header). Override with `SCOUT_CDP_URL`.

## Marriott: finding the cheapest stay

Three passes, coarse to fine, so a year of dates costs well under 100 requests. No manual setup: scout opens the pages it needs through marriott.com's own hotel search (this replaces the profile's "last search").

**1. Which months are cheap?** The low-rate calendar, one request per month. It shows the cheapest room on a standard rate, per night incl. the destination fee, before taxes: good for ranking months, not for pricing your room.

```bash
uv run scout marriott calendar --property BOBWI --from 2026-11 --to 2027-04 --nights 4 --adults 2
uv run scout marriott calendar --from 2027-05 --to 2027-10
uv run scout marriott calendar --from 2026-11 --to 2027-10 --stored   # whole window, no requests
```

**2. What does my room cost on those dates?** Exact totals (taxes and fees included) for the 3 cheapest calendar check-ins per month, one request per date. Filter by room afterwards for free; another room on the same rate plan is sometimes cheaper.

```bash
uv run scout marriott scan --from 2026-11-08 --to 2027-09-30 --calendar-top 3 --rate "Half Board"
uv run scout marriott report --from 2026-11-08 --to 2027-09-30 --calendar-top 3 \
  --room "Lagoon View Beach Villa" --rate "Half Board"
```

**3. Refine the best month.** Every check-in date of the 1–2 most promising months, since step 2 only samples:

```bash
uv run scout marriott scan --from 2027-03-01 --to 2027-03-31 --room "Lagoon View Beach Villa" --rate "Half Board"
```

Asking an agent "find the cheapest Half Board week at the Westin Bora Bora" runs the same steps (repo skill `hotel-price-scout`).

### Notes

- Each scanned date stores every room × rate in `data/scout.sqlite` (`SCOUT_DB_PATH`), so `report` and `calendar --stored` re-filter without new requests. XPF totals are also shown in EUR (fixed peg).
- Requests are sequential, 2–4 s apart (`SCOUT_DELAY_MIN`/`SCOUT_DELAY_MAX`). Keep runs to about 6 calendar months or ~35 dates; once a burst of 7 quick calendar clicks got a 403 from Akamai. A failed request stops the run; check marriott.com in that Chrome before trying again.
- Member rates need a (free) Marriott Bonvoy account.
