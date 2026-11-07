import argparse
import asyncio
import logging
import sys
from datetime import date, timedelta

from scout.cdp import ScoutError
from scout.sites import marriott


def _dates(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def _print_report(rows: list[marriott.Best]) -> None:
    priced = [r for r in rows if r.offer]
    low = min((r.offer.total for r in priced), default=None)
    print(f"{'Check-in':<11} {'Check-out':<11} {'Total':>13} {'≈ EUR':>8}  Room · Rate")
    for r in rows:
        if not r.offer:
            print(
                f"{r.check_in:<11} {r.check_out:<11} {'—':>13} {'':>8}  no matching offer"
            )
            continue
        o = r.offer
        eur = f"{o.total / marriott.XPF_PER_EUR:,.0f}" if o.currency == "XPF" else ""
        mark = "  ← lowest" if o.total == low else ""
        print(
            f"{r.check_in:<11} {r.check_out:<11} {o.total:>9,.0f} {o.currency} {eur:>8}  "
            f"{o.room_name} · {o.rate_name} ({o.rate_code}){mark}"
        )


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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    check_ins = _dates(args.start, args.end)
    failure = None
    if args.action == "scan":
        try:
            asyncio.run(
                marriott.scan(args.property, check_ins, args.nights, args.adults)
            )
        except ScoutError as e:
            failure = f"scout: {e}"  # still report whatever was stored
    db = marriott.open_db()
    _print_report(
        marriott.best_per_date(
            db, args.property, check_ins, args.nights, args.adults, args.room, args.rate
        )
    )
    if failure:
        sys.exit(failure)
