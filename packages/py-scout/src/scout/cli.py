import argparse
import asyncio
import logging
import sys
from datetime import date, timedelta

from scout.cdp import ScoutError
from scout.sites.marriott import calendar, eur, rates


def _dates(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _check_ins(args: argparse.Namespace) -> list[date]:
    if not args.calendar_top:
        return _dates(args.start, args.end)
    db = calendar.open_db()
    picked = calendar.cheapest_dates(
        db,
        args.property,
        args.start,
        args.end,
        args.nights,
        args.adults,
        args.calendar_top,
    )
    if not picked:
        sys.exit(
            "scout: no stored calendar data for that range and party; run `scout marriott calendar` first"
        )
    return picked


def _month(value: str) -> date:
    return date.fromisoformat(f"{value}-01")


def _eur(amount: float, currency: str) -> str:
    value = eur(amount, currency)
    return f"≈ €{value:,.0f}" if value is not None else ""


def _print_rates(rows: list[rates.Best]) -> None:
    low = min((r.offer.total for r in rows if r.offer), default=None)
    print(f"{'Check-in':<11} {'Check-out':<11} {'Total':>13} {'':>8}  Room · Rate")
    for r in rows:
        if not r.offer:
            print(
                f"{r.check_in:<11} {r.check_out:<11} {'—':>13} {'':>8}  no matching offer"
            )
            continue
        o = r.offer
        mark = "  ← lowest" if o.total == low else ""
        print(
            f"{r.check_in:<11} {r.check_out:<11} {o.total:>9,.0f} {o.currency} {_eur(o.total, o.currency):>8}  "
            f"{o.room_name} · {o.rate_name} ({o.rate_code}){mark}"
        )


def _print_calendar(report: calendar.Report) -> None:
    if report.nights is None:
        print("No calendar data stored yet.")
        return
    priced = [m for m in report.months if m.nightly is not None]
    low = min((m.nightly for m in priced), default=None)
    print(
        f"Lowest nightly rate per month · {report.nights} nights, {report.guests} guests · cheapest room, standard rate"
    )
    print(f"{'Month':<9} {'From/night':>21}  Cheapest check-ins")
    for m in report.months:
        if m.nightly is None:
            print(f"{m.month:%b %Y}  {'—':>21}  no rates")
            continue
        days = ", ".join(f"{d:%b} {d.day}" for d in m.dates[:2])
        more = f" +{len(m.dates) - 2} more" if len(m.dates) > 2 else ""
        mark = "  ← lowest" if m.nightly == low else ""
        print(
            f"{m.month:%b %Y}  {m.nightly:>9,.0f} {m.currency} {_eur(m.nightly, m.currency):>7}  {days}{more}{mark}"
        )
    fee = next((m for m in priced if m.fee), None)
    print(
        f"Incl. {fee.fee:,.0f} {fee.currency}/night destination fee, before taxes, as the calendar page shows."
        if fee
        else "Before taxes and fees."
    )
    print("For a specific room and rate, run `scout marriott scan` on a cheap month.")


def _print_changes(result: rates.Changes, min_pct: float) -> None:
    if not result.compared:
        print(
            "No check-in date has been scanned twice yet. Re-run `scout marriott scan` "
            "on the same dates later to start tracking."
        )
        return
    print(
        f"Price changes of {min_pct:g}% or more · latest vs previous scan of each check-in"
    )
    if not result.changes:
        print("None.")
    else:
        print(
            f"{'Check-in':<11} {'Before':>9} → {'Now':>13}  {'Change':<18} Room · Rate"
        )
    for c in result.changes:
        before = f"{c.before:,.0f}" if c.before is not None else "—"
        now = f"{c.after:,.0f} {c.currency}" if c.after is not None else "—"
        if c.pct is None:
            change = "new" if c.before is None else "gone"
        else:
            diff = eur(c.after - c.before, c.currency)
            change = f"{c.pct:+.1f}%" + (
                f" ≈ {'+' if diff >= 0 else '−'}€{abs(diff):,.0f}"
                if diff is not None
                else ""
            )
        print(
            f"{c.check_in:<11} {before:>9} → {now:>13}  {change:<18} {c.room_name} · {c.rate_name} ({c.rate_code})"
        )
    single = f"; {result.single} scanned only once" if result.single else ""
    print(f"{result.compared} check-in dates compared{single}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scout", description="Price scans through your own Chrome over CDP"
    )
    sites = parser.add_subparsers(dest="site", required=True)
    mar = sites.add_parser("marriott", help="Marriott room rates")
    actions = mar.add_subparsers(dest="action", required=True)
    for name, help_ in [
        ("scan", "fetch rates for each check-in date, then report"),
        ("report", "report from stored scans"),
    ]:
        p = actions.add_parser(name, help=help_)
        p.add_argument(
            "--property",
            default="BOBWI",
            help="MARSHA code (default: BOBWI, Westin Bora Bora)",
        )
        p.add_argument(
            "--from",
            dest="start",
            type=date.fromisoformat,
            required=True,
            help="first check-in date",
        )
        p.add_argument(
            "--to",
            dest="end",
            type=date.fromisoformat,
            required=True,
            help="last check-in date",
        )
        p.add_argument("--nights", type=int, default=4)
        p.add_argument("--adults", type=int, default=2)
        p.add_argument(
            "--room",
            default="",
            help="room name contains, e.g. 'Lagoon View Beach Villa'",
        )
        p.add_argument(
            "--rate", default="", help="rate name contains, e.g. 'Half Board'"
        )
        p.add_argument(
            "--calendar-top",
            type=int,
            default=0,
            metavar="N",
            help="only the N cheapest check-ins per month from stored calendar data",
        )
    p = actions.add_parser(
        "calendar", help="lowest nightly rate per month from the low-rate calendar"
    )
    p.add_argument(
        "--property",
        default="BOBWI",
        help="MARSHA code (default: BOBWI, Westin Bora Bora)",
    )
    p.add_argument(
        "--from", dest="start", type=_month, required=True, help="first month, YYYY-MM"
    )
    p.add_argument(
        "--to", dest="end", type=_month, required=True, help="last month, YYYY-MM"
    )
    p.add_argument("--nights", type=int, default=4)
    p.add_argument("--adults", type=int, default=2)
    p.add_argument(
        "--stored", action="store_true", help="report stored data only, no requests"
    )
    p = actions.add_parser(
        "changes", help="price moves between the last two scans of each check-in date"
    )
    p.add_argument("--property", default="BOBWI", help="MARSHA code (default: BOBWI)")
    p.add_argument("--from", dest="start", type=date.fromisoformat, default=date.min)
    p.add_argument("--to", dest="end", type=date.fromisoformat, default=date.max)
    p.add_argument("--nights", type=int, default=4)
    p.add_argument("--adults", type=int, default=2)
    p.add_argument("--room", default="", help="room name contains")
    p.add_argument("--rate", default="", help="rate name contains")
    p.add_argument(
        "--min-change", type=float, default=3.0, metavar="PCT", help="default: 3"
    )
    args = parser.parse_args()

    if args.action == "changes":
        result = rates.price_changes(
            rates.open_db(),
            args.property,
            args.start,
            args.end,
            args.nights,
            args.adults,
            args.room,
            args.rate,
            args.min_change,
        )
        _print_changes(result, args.min_change)
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.action in ("scan", "report"):
        check_ins = _check_ins(args)
    failure = None
    try:
        if args.action == "scan":
            asyncio.run(rates.scan(args.property, check_ins, args.nights, args.adults))
        elif args.action == "calendar" and not args.stored:
            asyncio.run(
                calendar.fetch(
                    args.property, args.start, args.end, args.nights, args.adults
                )
            )
    except ScoutError as e:
        failure = f"scout: {e}"  # still report whatever was stored

    if args.action == "calendar":
        _print_calendar(
            calendar.monthly_lows(
                calendar.open_db(), args.property, args.start, args.end
            )
        )
    else:
        rows = rates.best_per_date(
            rates.open_db(),
            args.property,
            check_ins,
            args.nights,
            args.adults,
            args.room,
            args.rate,
        )
        _print_rates(rows)
    if failure:
        sys.exit(failure)
