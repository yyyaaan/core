---
name: hotel-price-scout
description: Find the cheapest dates and exact prices for a Marriott hotel stay (specific room, rate plan such as Half Board, taxes and fees included) with packages/py-scout through the user's own debug Chrome. Use when asked about hotel prices, cheapest or flexible dates for a trip, monthly price overviews, or to run scout.
---

# Hotel price scout

Goal: the cheapest check-in dates for the user's exact room and rate plan, with real totals, using few requests. Three passes, coarse to fine: calendar overview → exact prices on the calendar's cheapest dates → full scan of the best month(s). Mechanics and site quirks are in `packages/py-scout/AGENTS.md`; read it first.

## 0. Preconditions

- Chrome on the Mac with remote debugging (command in `packages/py-scout/README.md`). Check: `curl -s http://$(getent hosts host.docker.internal | cut -d' ' -f1):9222/json/version`. If it's down, give the user the command; don't try to start Chrome from the container.
- Pin down with the user: hotel (MARSHA code, e.g. `BOBWI`; it's in the hotel's marriott.com URL), nights, adults, room name, rate plan (e.g. "Half Board"), and the window of acceptable dates. The booking window is about 351 days from today.
- Each run replaces marriott.com's "last search" in the debug profile. Mention it once.

## 1. Overview: calendar (1 request per month)

```bash
uv run scout marriott calendar --property BOBWI --from 2027-05 --to 2027-10 --nights 4 --adults 2
uv run scout marriott calendar --from 2026-11 --to 2027-10 --stored   # whole window, no requests
```

- At most about 6 months per run. Cover the whole window in several runs, then print it all with `--stored`.
- This is the cheapest room on a standard rate, per night incl. the destination fee, before taxes. Say so whenever you show it: it ranks months, it doesn't price the user's room.

## 2. Dive: exact prices on the calendar's cheapest dates

```bash
uv run scout marriott scan --from 2026-11-08 --to 2027-09-30 --calendar-top 3 --rate "Half Board"
uv run scout marriott report --from 2026-11-08 --to 2027-09-30 --calendar-top 3 --room "Lagoon View Beach Villa" --rate "Half Board"
```

- `--calendar-top 3` = the 3 cheapest calendar check-ins per month (~33 requests for a year). It needs calendar data for the same nights and adults.
- Scan with the rate filter only, then `report` (no requests) once per view: the user's room, and any room. A different room on the same rate plan is often cheaper in some seasons and worth showing.
- If the target room shows "no matching offer", check whether it's sold out or only missing that rate:

  ```bash
  uv run python -c "import sqlite3; db=sqlite3.connect('packages/py-scout/data/scout.sqlite'); print(db.execute(\"SELECT DISTINCT rate_name FROM marriott_offers WHERE check_in='2026-12-11' AND room_name LIKE '%Lagoon View Beach Villa%'\").fetchall())"
  ```

## 3. Refine: full month(s)

The calendar ranks months by the cheapest room, not the user's, so the top 3 dates are a sample. For the 1–2 best months, scan every day (~30 requests each, about 2 minutes):

```bash
uv run scout marriott scan --from 2027-03-01 --to 2027-03-31 --room "Lagoon View Beach Villa" --rate "Half Board"
```

## Request budget and blocks

- Requests are sequential with 2–4 s pauses. Keep each run to about 35 requests. Ask before going beyond about 100 in a session.
- A 403 or a failed request stops scout. Stop there too: tell the user, ask them to check marriott.com in that Chrome, and don't retry in a loop or change pacing or headers to get through.
- Re-filtering costs nothing: everything is stored, so use `report` and `--stored` rather than scanning again.

## Report

- Lead with the answer: the cheapest date(s) for the user's room and rate, total incl. taxes and fees, in the hotel currency and ≈ EUR.
- Then compact tables: monthly overview (labelled as cheapest room, before taxes), the target room's best dates, and any cheaper room on the same rate plan.
- Flag member rates (need a free Marriott Bonvoy account), dates where the room isn't offered, and the sampling limit when only `--calendar-top` was used.
- Suggest the next pass (refine the best month), with the exact command.
