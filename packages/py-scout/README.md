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

## Marriott

Once per profile, search the hotel on marriott.com in that Chrome until room rates show (any dates). Then:

```bash
uv run scout marriott scan --property BOBWI --from 2027-10-01 --to 2027-10-31 --nights 4 --adults 2 \
  --room "Lagoon View Beach Villa" --rate "Half Board"
uv run scout marriott report --from 2027-10-01 --to 2027-10-31 --rate "Half Board"   # from stored scans, no requests
```

Monthly overview from the low-rate calendar (cheapest room, standard rate, before taxes; one request per month):

```bash
uv run scout marriott calendar --from 2027-05 --to 2027-10 --nights 4 --adults 2
uv run scout marriott calendar --from 2026-11 --to 2027-10 --stored   # whole window, no requests
```

No manual setup: scout loads a hotel search URL with your nights and guests (that sets marriott.com's "last search" in the profile), opens the calendar on the first month and clicks forward. Keep ranges to about 6 months per run: an earlier run got a 403 from Akamai after 7 quick clicks; two 6-month runs went through fine.

One request per check-in date returns every room × rate, all stored in `data/scout.sqlite` (`SCOUT_DB_PATH`), so `report` can filter differently without scanning again. Totals are the grand total incl. taxes and fees, as the site shows them; XPF is also shown in EUR (fixed peg). Requests are paced 2–4 s apart (`SCOUT_DELAY_MIN`/`SCOUT_DELAY_MAX`), and a failed request stops the scan.
