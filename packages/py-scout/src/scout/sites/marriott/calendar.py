"""Marriott low-rate calendar: lowest nightly rate per check-in date, about a month per request.

Only the cheapest room on a standard rate, before taxes (no packages such as Half Board):
it shows which months are cheap, not what a given room costs. The calendar page reads
nights, guests and its first month from the session's search, so scout first loads a
hotel search URL (as the site's own search form builds it), then the calendar. Its query
isn't kept in Apollo's registry, so scout clicks through months like a person and reads
the responses the page receives.
"""

import asyncio
import logging
import random
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlencode

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, Response

from scout import cdp, store
from scout.cdp import ScoutError
from scout.config import get_settings

log = logging.getLogger(__name__)

CALENDAR_OPERATION = "phoenixShopADFSearchProductsByProperty"
FEE_OPERATION = "phoenixShopHQVRateOnly"
SEARCH_URL = "https://www.marriott.com/search/findHotels.mi"
# a Bora Bora flexible-dates search as the site's form submits it; search_url() adds dates and party.
# The calendar picks the hotel by propertyCode, so the destination here only has to be valid.
SEARCH_PARAMS = {
    "flexibleDateSearch": "true",
    "childrenCountBox": "0 Children Per Room",
    "childrenCount": "0",
    "clusterCode": "none",
    "useRewardsPoints": "false",
    "isAdvanceSearch": "true",
    "isNGSF": "false",
    "recordsPerPage": "20",
    "destinationAddress.type": "Hotel Name",
    "destinationAddress.latitude": "-16.497141499999998",
    "isInternalSearch": "true",
    "vsInitialRequest": "false",
    "searchType": "InCity",
    "destinationAddress.stateProvinceDisplayName": "Leeward Islands",
    "countryName": "PF",
    "destinationAddress.stateProvince": "Leeward Islands",
    "searchRadius": "50",
    "singleSearchAutoSuggest": "Unmatched",
    "destinationAddress.placeId": "ChIJx-RZnHCXvXYR95AaxgOP5OY",
    "for-hotels-nearme": "Near",
    "destinationAddress.country": "PF",
    "destinationAddress.address": "MOTU TAPE, BP 190, Bora-Bora 98730, French Polynesia",
    "collapseAccordian": "is-hidden",
    "singleSearch": "true",
    "destinationAddress.secondaryText": "Leeward Islands, PF",
    "destinationAddress.city": "Bora-Bora",
    "destinationAddress.mainText": "Bora-Bora",
    "isTransient": "true",
    "destinationAddress.longitude": "-151.7018508",
    "initialRequest": "false",
    "flexibleDateSearchRateDisplay": "false",
    "isSearch": "true",
    "isRateCalendar": "true",
    "destinationAddress.destination": "The Westin Bora Bora Resort Spa",
    "isHideFlexibleDateCalendar": "false",
    "roomCountBox": "1 Room",
    "roomCount": "1",
    "deviceType": "desktop-web",
    "view": "list",
}
CALENDAR_URL = (
    "https://www.marriott.com/search/availabilityCalendar.mi"
    "?isRateCalendar=true&isSearch=true&propertyCode={}"
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS marriott_calendar (
    scanned_at TEXT NOT NULL,
    property_id TEXT NOT NULL,
    check_in TEXT NOT NULL,
    nights INTEGER NOT NULL,
    guests INTEGER NOT NULL,
    currency TEXT NOT NULL,
    avg_nightly REAL NOT NULL,  -- lowest standard rate, before taxes and fees
    nightly_fee REAL  -- mandatory (destination) fee per night, if the page reported it
);
CREATE INDEX IF NOT EXISTS marriott_calendar_search
    ON marriott_calendar (property_id, nights, guests, check_in, scanned_at);
"""


@dataclass(frozen=True)
class Day:
    check_in: date
    currency: str
    avg_nightly: float


@dataclass(frozen=True)
class MonthLow:
    month: date
    currency: str | None = None
    nightly: float | None = None  # incl. the fee when known, as the page shows it
    fee: float | None = None
    dates: list[date] = field(default_factory=list)


@dataclass(frozen=True)
class Report:
    nights: int | None
    guests: int | None
    months: list[MonthLow]


def _amount(money: dict) -> float:
    return money["amount"] / 10 ** (money.get("decimalPoint") or 0)


def months(first: date, last: date) -> list[date]:
    out, m = [], first.replace(day=1)
    while m <= last:
        out.append(m)
        m = (m + timedelta(days=32)).replace(day=1)
    return out


def parse_calendar(data: dict) -> list[Day]:
    """One Day per check-in date; the API returns runs of dates sharing a price."""
    days = []
    for edge in data["search"]["calendarSearchByProperty"].get("edges") or []:
        try:
            node = edge["node"]
            money = node["rateModes"]["lowestAverageRate"]["amount"]
            start = date.fromisoformat(node["startDate"])
            end = date.fromisoformat(node["endDate"])
        except (KeyError, TypeError, ValueError) as e:
            log.warning("skipping unparsable calendar run: %r", e)
            continue
        for i in range((end - start).days + 1):
            days.append(
                Day(start + timedelta(days=i), money["currency"], _amount(money))
            )
    return days


def parse_fee(data: dict) -> float | None:
    """Mandatory (destination) fee per night from the page's lowest-rate lookup."""
    try:
        for edge in data["search"]["lowestAvailableRates"]["searchByPropertyIds"][
            "edges"
        ]:
            for rate in edge["node"]["rates"]:
                fee = (rate["rateModes"].get("lowestAverageRate") or {}).get(
                    "mandatoryFees"
                )
                if fee:
                    return _amount(fee)
    except KeyError, TypeError:
        pass
    return None


def open_db() -> sqlite3.Connection:
    return store.open_db(get_settings().db_path, SCHEMA)


def save(
    db: sqlite3.Connection,
    property_id: str,
    nights: int,
    guests: int,
    days: list[Day],
    fee: float | None,
    scanned_at: datetime | None = None,
):
    scanned = (scanned_at or datetime.now(UTC)).isoformat(timespec="seconds")
    db.executemany(
        "INSERT INTO marriott_calendar VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                scanned,
                property_id,
                d.check_in.isoformat(),
                nights,
                guests,
                d.currency,
                d.avg_nightly,
                fee,
            )
            for d in days
        ],
    )
    db.commit()


def monthly_lows(
    db: sqlite3.Connection, property_id: str, first: date, last: date
) -> Report:
    """Lowest nightly rate per month and the check-in dates that have it, from each date's latest fetch.

    Uses the nights/guests of the most recent fetch, so older searches don't mix in.
    """
    latest = db.execute(
        "SELECT nights, guests FROM marriott_calendar WHERE property_id = ? ORDER BY scanned_at DESC LIMIT 1",
        (property_id,),
    ).fetchone()
    if not latest:
        return Report(None, None, [MonthLow(m) for m in months(first, last)])
    nights, guests = latest
    out = []
    for month in months(first, last):
        next_month = (month + timedelta(days=32)).replace(day=1)
        rows = db.execute(
            """
            SELECT check_in, currency, avg_nightly, nightly_fee FROM marriott_calendar c
            WHERE property_id = ? AND nights = ? AND guests = ? AND check_in >= ? AND check_in < ?
              AND scanned_at = (
                SELECT MAX(scanned_at) FROM marriott_calendar
                WHERE property_id = c.property_id AND nights = c.nights
                  AND guests = c.guests AND check_in = c.check_in)
            """,
            (property_id, nights, guests, month.isoformat(), next_month.isoformat()),
        ).fetchall()
        if not rows:
            out.append(MonthLow(month))
            continue
        low = min(r["avg_nightly"] for r in rows)
        cheapest = [r for r in rows if r["avg_nightly"] == low]
        fee = cheapest[0]["nightly_fee"]
        out.append(
            MonthLow(
                month=month,
                currency=cheapest[0]["currency"],
                nightly=low + (fee or 0),
                fee=fee,
                dates=sorted({date.fromisoformat(r["check_in"]) for r in cheapest}),
            )
        )
    return Report(nights, guests, out)


def _is(operation: str) -> Callable[[Response], bool]:
    return lambda r: f"/mi/query/{operation}" in r.url


def search_url(check_in: date, nights: int, adults: int) -> str:
    def us(d: date) -> str:
        return d.strftime("%m/%d/%Y")

    check_out = check_in + timedelta(days=nights)
    return f"{SEARCH_URL}?" + urlencode(
        {
            **SEARCH_PARAMS,
            "fromDate": us(check_in),
            "fromDateDefaultFormat": us(check_in),
            "t-start": us(check_in),
            "toDate": us(check_out),
            "toDateDefaultFormat": us(check_out),
            "t-end": us(check_out),
            "fromToDate_submit": us(check_out),
            "lengthOfStay": str(nights),
            "numAdultsPerRoom": str(adults),
            "guestCountBox": f"{adults} Adult Per Room",
        }
    )


async def _shown_month(page: Page) -> date:
    text = await page.locator(".DayPicker-Caption").first.inner_text()
    return datetime.strptime(text.strip(), "%B %Y").date()


async def _read(response: Response) -> tuple[int, int, list[Day]]:
    if not response.ok:
        raise ScoutError(f"calendar request returned {response.status}, stopping")
    options = response.request.post_data_json["variables"]["search"]["options"]
    days = parse_calendar((await response.json())["data"])
    return options["numberOfDays"], options["numberInParty"], days


async def fetch(
    property_id: str, first: date, last: date, nights: int, guests: int
) -> None:
    """Fetch every calendar month between first and last (month starts), then store them.

    Sets the session search first (this changes what marriott.com shows as the last search),
    and stops before any month click if the calendar isn't showing the expected nights/guests.
    """
    settings = get_settings()
    found: dict[date, Day] = {}
    fees: list[float] = []
    search: tuple[int, int] | None = None

    async def on_response(response: Response):
        if _is(FEE_OPERATION)(response) and response.ok:
            if (
                fee := parse_fee((await response.json()).get("data") or {})
            ) is not None:
                fees.append(fee)

    def keep(nights: int, guests: int, days: list[Day]):
        nonlocal search
        search = search or (nights, guests)
        found.update((d.check_in, d) for d in days)

    # the calendar opens on the search's month; tomorrow at the earliest
    check_in = max(first, date.today() + timedelta(days=1))
    async with cdp.connect() as browser:
        page = await browser.contexts[0].new_page()
        page.on("response", on_response)
        try:
            try:
                await page.goto(search_url(check_in, nights, guests))
                async with page.expect_response(_is(CALENDAR_OPERATION)) as info:
                    await page.goto(CALENDAR_URL.format(property_id))
                keep(*await _read(await info.value))
                shown = await _shown_month(page)
            except PlaywrightError as e:
                raise ScoutError(f"calendar didn't load: {e}") from e
            log.info("calendar opened at %s", f"{shown:%b %Y}")
            if search != (nights, guests):
                found.clear()  # don't store a different search
                raise ScoutError(
                    f"calendar shows {search[0]} nights, {search[1]} guests, not {nights} and {guests}. "
                    "The site may have changed its search URL; see SEARCH_PARAMS."
                )

            # each click is a request (revisits refetch), so do the nearer end first, then sweep
            for target in sorted((first, last), key=lambda m: abs((m - shown).days)):
                while shown != target:
                    step = "next" if target > shown else "prev"
                    button = page.locator(f".DayPicker-NavButton--{step}")
                    if (
                        not await button.count()
                        or await button.get_attribute("aria-disabled") == "true"
                    ):
                        log.info("calendar can't go %s from %s", step, f"{shown:%b %Y}")
                        break
                    await asyncio.sleep(
                        random.uniform(settings.delay_min, settings.delay_max)
                    )
                    try:
                        async with page.expect_response(
                            _is(CALENDAR_OPERATION), timeout=20_000
                        ) as info:
                            await button.evaluate("el => el.click()")
                        result = await _read(await info.value)
                        now_shown = await _shown_month(page)
                    except PlaywrightError as e:
                        raise ScoutError(
                            f"calendar request failed, stopping: {e}"
                        ) from e
                    keep(*result)
                    log.info(
                        "%s: %d check-in dates", f"{now_shown:%b %Y}", len(result[2])
                    )
                    stuck, shown = now_shown == shown, now_shown
                    if stuck or (step == "next" and not result[2]):
                        break  # past the booking window
        finally:
            await page.close()
            if found and search:
                save(
                    open_db(),
                    property_id,
                    *search,
                    list(found.values()),
                    fees[-1] if fees else None,
                )
