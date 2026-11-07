import json
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import pytest

from scout import store
from scout.sites.marriott import calendar

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def october() -> dict:
    # real response for the October 2027 view (4 nights, 2 guests), Westin Bora Bora
    return json.loads((FIXTURES / "marriott_calendar_bobwi_202710.json").read_text())[
        "response"
    ]["data"]


def test_parse_calendar_expands_runs(october):
    days = {d.check_in: d for d in calendar.parse_calendar(october)}
    assert min(days) == date(2027, 9, 26)
    assert max(days) == date(2027, 10, 22)
    assert len(days) == 27  # every grid date up to the end of the booking window
    # run 2027-10-03..10-06 shares one price; the page adds the 11,990 fee: 188,390
    assert {days[date(2027, 10, d)].avg_nightly for d in range(3, 7)} == {176400.0}
    assert days[date(2027, 10, 1)].currency == "XPF"


def test_parse_fee():
    data = json.loads((FIXTURES / "marriott_hqv_bobwi_20270926.json").read_text())[
        "data"
    ]
    assert calendar.parse_fee(data) == 11990.0
    assert calendar.parse_fee({}) is None


def test_months():
    assert calendar.months(date(2027, 11, 1), date(2028, 2, 1)) == [
        date(2027, 11, 1),
        date(2027, 12, 1),
        date(2028, 1, 1),
        date(2028, 2, 1),
    ]


def test_monthly_lows(october, tmp_path):
    db = store.open_db(tmp_path / "t.sqlite", calendar.SCHEMA)
    days = calendar.parse_calendar(october)
    calendar.save(
        db, "BOBWI", 4, 2, days, 11990.0, scanned_at=datetime(2026, 11, 1, tzinfo=UTC)
    )

    report = calendar.monthly_lows(db, "BOBWI", date(2027, 9, 1), date(2027, 11, 1))
    assert (report.nights, report.guests) == (4, 2)
    sep, octo, nov = report.months
    assert sep.nightly == 172970.0 + 11990  # only Sep 26-30 known
    assert octo.nightly == 171000.0 + 11990  # the page's "LOW" Fridays: 182,990
    assert octo.dates == [date(2027, 10, d) for d in (1, 8, 15, 22)]
    assert nov.nightly is None and nov.dates == []


def test_monthly_lows_prefers_latest_search(october, tmp_path):
    db = store.open_db(tmp_path / "t.sqlite", calendar.SCHEMA)
    days = calendar.parse_calendar(october)
    calendar.save(
        db, "BOBWI", 4, 2, days, None, scanned_at=datetime(2026, 11, 1, tzinfo=UTC)
    )
    calendar.save(
        db, "BOBWI", 5, 2, days[:3], None, scanned_at=datetime(2026, 11, 2, tzinfo=UTC)
    )

    report = calendar.monthly_lows(db, "BOBWI", date(2027, 10, 1), date(2027, 10, 1))
    assert report.nights == 5
    assert report.months[0].nightly is None  # 5-night data only covers Sep 26-28


def test_monthly_lows_empty(tmp_path):
    db = store.open_db(tmp_path / "t.sqlite", calendar.SCHEMA)
    report = calendar.monthly_lows(db, "BOBWI", date(2027, 6, 1), date(2027, 7, 1))
    assert report.nights is None and len(report.months) == 2


def test_search_url():
    url = calendar.search_url(date(2027, 5, 3), 4, 2)
    params = dict(parse_qsl(urlsplit(url).query))
    assert url.startswith("https://www.marriott.com/search/findHotels.mi?")
    assert params["fromDate"] == "05/03/2027" and params["toDate"] == "05/07/2027"
    assert params["lengthOfStay"] == "4" and params["numAdultsPerRoom"] == "2"
    assert params["isRateCalendar"] == "true" and params["flexibleDateSearch"] == "true"
