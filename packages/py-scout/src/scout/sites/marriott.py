"""Marriott room rates per check-in date, via the rate list page's own GraphQL client.

The site sits behind Akamai Bot Manager, so requests only work from inside a real
browser tab. Instead of rebuilding the request (safelisted query, signed headers),
we ask the page's Apollo client to run its own query again with other dates.
"""

import asyncio
import logging
import random
import sqlite3
from dataclasses import astuple, dataclass, fields
from datetime import UTC, date, datetime, timedelta

from playwright.async_api import Browser, Page
from playwright.async_api import Error as PlaywrightError

from scout import cdp, store
from scout.cdp import ScoutError
from scout.config import get_settings

log = logging.getLogger(__name__)

OPERATION = "PhoenixBookDTTSearchProductsByProperty"
RATE_LIST_URL = "https://www.marriott.com/reservation/rateListMenu.mi"
XPF_PER_EUR = 1000 / 8.38  # fixed peg

# finds the rate list query the page itself registered (its document, variables and headers)
_FIND_QUERY_JS = """
const findQuery = op => [...(window.__APOLLO_CLIENT__?.queryManager.queries.values() ?? [])].find(q =>
  q.observableQuery && q.document.definitions.some(d => d.kind === 'OperationDefinition' && d.name?.value === op));
"""
READY_JS = f"op => {{ {_FIND_QUERY_JS} return !!findQuery(op); }}"
QUERY_JS = f"""
async ({{operation, propertyId, startDate, endDate, adults}}) => {{
  {_FIND_QUERY_JS}
  const q = findQuery(operation);
  if (!q) throw new Error(`${{operation}} is not registered on this page`);
  const variables = structuredClone(q.variables);
  variables.search.propertyId = propertyId;
  Object.assign(variables.search.options, {{startDate, endDate, numberInParty: adults}});
  const r = await window.__APOLLO_CLIENT__.query({{
    query: q.document, variables, context: q.observableQuery.options.context,
    fetchPolicy: 'no-cache', errorPolicy: 'all',
  }});
  return {{data: r.data, errors: (r.errors ?? []).map(e => e.message)}};
}}
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS marriott_offers (
    scanned_at TEXT NOT NULL,
    property_id TEXT NOT NULL,
    check_in TEXT NOT NULL,
    check_out TEXT NOT NULL,
    adults INTEGER NOT NULL,
    room_name TEXT NOT NULL,
    room_description TEXT,
    rate_name TEXT NOT NULL,
    rate_code TEXT,
    rate_category TEXT,
    members_only INTEGER,
    currency TEXT NOT NULL,
    avg_nightly REAL,
    subtotal REAL,
    fees REAL,
    total REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS marriott_offers_search
    ON marriott_offers (property_id, check_in, check_out, adults, scanned_at);
"""


@dataclass(frozen=True)
class Offer:
    room_name: str
    room_description: str
    rate_name: str
    rate_code: str
    rate_category: str
    members_only: bool
    currency: str
    avg_nightly: float | None
    subtotal: float | None
    fees: float | None
    total: float  # grand total incl. taxes and fees


@dataclass(frozen=True)
class Best:
    check_in: str
    check_out: str
    offer: Offer | None


def _money(node: dict | None, *path: str) -> float | None:
    for key in path:
        node = (node or {}).get(key)
    if not node:
        return None
    return node["amount"] / 10 ** (node.get("decimalPoint") or 0)


def parse_offers(data: dict) -> tuple[list[Offer], list[str]]:
    """Room/rate offers and status errors (e.g. dates outside the booking window)."""
    result = data["commerce"]["product"]["searchProductsByProperty"]
    errors = [
        e.get("devMessage") or e.get("message") or e.get("code")
        for e in result.get("errors") or []
    ]
    offers: dict[tuple, Offer] = {}
    for edge in result.get("edges") or []:
        try:
            node = edge["node"]
            info = node["basicInformation"]
            rate_plans = info.get("ratePlan") or [{}]
            total = _money(node, "totalPricing", "rateModes", "grandTotal", "amount")
            if total is None:
                continue
            offer = Offer(
                room_name=info["name"],
                room_description=info.get("description") or "",
                rate_name=node["rates"]["name"],
                rate_code=rate_plans[0].get("ratePlanCode") or "",
                rate_category=(node.get("availabilityAttributes") or {})
                .get("productRateCategory", {})
                .get("typeCode")
                or "",
                members_only=bool(info.get("isMembersOnly")),
                currency=node["totalPricing"]["rateModes"]["grandTotal"]["amount"][
                    "currency"
                ],
                avg_nightly=_money(
                    node, "rates", "rateModes", "averageNightlyRatePerUnit", "amount"
                ),
                subtotal=_money(
                    node, "totalPricing", "rateModes", "subtotalPerQuantity", "amount"
                ),
                fees=_money(
                    node,
                    "totalPricing",
                    "rateModes",
                    "totalMandatoryFeesPerQuantity",
                    "amount",
                ),
                total=total,
            )
        except (KeyError, TypeError, IndexError) as e:
            log.warning(
                "skipping unparsable offer %s: %r", edge.get("node", {}).get("id"), e
            )
            continue
        offers.setdefault(
            (offer.room_name, offer.rate_code, offer.total), offer
        )  # API repeats some rows
    return list(offers.values()), errors


def open_db() -> sqlite3.Connection:
    return store.open_db(get_settings().db_path, SCHEMA)


def save(
    db: sqlite3.Connection,
    property_id: str,
    check_in: date,
    check_out: date,
    adults: int,
    offers: list[Offer],
    scanned_at: datetime | None = None,
):
    scanned = (scanned_at or datetime.now(UTC)).isoformat(timespec="seconds")
    cols = ", ".join(
        [
            "scanned_at",
            "property_id",
            "check_in",
            "check_out",
            "adults",
            *(f.name for f in fields(Offer)),
        ]
    )
    marks = ", ".join("?" * (5 + len(fields(Offer))))
    db.executemany(
        f"INSERT INTO marriott_offers ({cols}) VALUES ({marks})",
        [
            (
                scanned,
                property_id,
                check_in.isoformat(),
                check_out.isoformat(),
                adults,
                *astuple(o),
            )
            for o in offers
        ],
    )
    db.commit()


def best_per_date(
    db: sqlite3.Connection,
    property_id: str,
    check_ins: list[date],
    nights: int,
    adults: int,
    room: str = "",
    rate: str = "",
) -> list[Best]:
    """Cheapest offer per check-in date from each date's latest scan, filtered by room/rate substrings."""
    names = [f.name for f in fields(Offer)]
    out = []
    for check_in in check_ins:
        check_out = check_in + timedelta(days=nights)
        key = (property_id, check_in.isoformat(), check_out.isoformat(), adults)
        row = db.execute(
            f"""
            SELECT {", ".join(names)} FROM marriott_offers
            WHERE property_id = ? AND check_in = ? AND check_out = ? AND adults = ?
              AND scanned_at = (
                SELECT MAX(scanned_at) FROM marriott_offers
                WHERE property_id = ? AND check_in = ? AND check_out = ? AND adults = ?)
              AND room_name LIKE ? AND rate_name LIKE ?
            ORDER BY total LIMIT 1
            """,
            (*key, *key, f"%{room}%", f"%{rate}%"),
        ).fetchone()
        out.append(
            Best(
                check_in.isoformat(),
                check_out.isoformat(),
                Offer(**dict(row)) if row else None,
            )
        )
    return out


async def _rate_list_page(browser: Browser) -> Page:
    for page in cdp.pages(browser):
        if "/reservation/rateListMenu.mi" in page.url and await page.evaluate(
            READY_JS, OPERATION
        ):
            return page
    # the page renders the session's last search; we only need its client and query
    page = await browser.contexts[0].new_page()
    await page.goto(RATE_LIST_URL)
    try:
        await page.wait_for_function(READY_JS, arg=OPERATION, timeout=30_000)
    except PlaywrightError as e:
        raise ScoutError(
            "No usable Marriott rate list tab. Search the hotel on marriott.com in the debug Chrome "
            "until room rates show (any dates), then retry."
        ) from e
    return page


async def scan(
    property_id: str, check_ins: list[date], nights: int, adults: int
) -> None:
    settings = get_settings()
    db = open_db()
    async with cdp.connect() as browser:
        page = await _rate_list_page(browser)
        for i, check_in in enumerate(check_ins):
            if i:
                await asyncio.sleep(
                    random.uniform(settings.delay_min, settings.delay_max)
                )
            check_out = check_in + timedelta(days=nights)
            args = {
                "operation": OPERATION,
                "propertyId": property_id,
                "startDate": check_in.isoformat(),
                "endDate": check_out.isoformat(),
                "adults": adults,
            }
            try:
                res = await page.evaluate(QUERY_JS, args)
            except PlaywrightError as e:
                # blocked or challenged: stop rather than keep hammering
                raise ScoutError(
                    f"{check_in}: request failed, stopping scan: {e}"
                ) from e
            offers, errors = (
                parse_offers(res["data"])
                if res.get("data")
                else ([], res.get("errors") or ["no data"])
            )
            if offers:
                save(db, property_id, check_in, check_out, adults, offers)
            log.info(
                "%s → %s: %d offers%s",
                check_in,
                check_out,
                len(offers),
                f" ({'; '.join(errors)})" if errors else "",
            )
