import json
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from scout import store
from scout.sites.marriott import rates

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def products() -> dict:
    # trimmed real response: Westin Bora Bora, 2027-09-20 → 09-24, 2 adults
    return json.loads((FIXTURES / "marriott_products_bobwi_20270920.json").read_text())


def test_parse_offers(products):
    offers, errors = rates.parse_offers(products)
    assert errors == []
    assert len(offers) == 4  # one duplicated row dropped
    half_board = next(o for o in offers if o.rate_code == "ECPZ")
    assert half_board.room_name == "Lagoon View Beach Villa"
    assert half_board.rate_name == "Half Board Haven"
    assert half_board.currency == "XPF"
    assert half_board.total == 811507  # what the page shows "with taxes and fees"


def test_parse_offers_skips_broken_edge(products):
    edges = products["commerce"]["product"]["searchProductsByProperty"]["edges"]
    del edges[0]["node"]["basicInformation"]
    offers, _ = rates.parse_offers(products)
    assert len(offers) == 3


def test_parse_offers_outside_booking_window():
    data = {
        "commerce": {
            "product": {
                "searchProductsByProperty": {
                    "edges": None,
                    "errors": [
                        {
                            "code": "UER30003",
                            "devMessage": "Invalid End Date",
                            "message": "unexpected error",
                        }
                    ],
                }
            }
        }
    }
    assert rates.parse_offers(data) == ([], ["Invalid End Date"])


def test_best_per_date_uses_latest_scan(products, tmp_path):
    db = store.open_db(tmp_path / "t.sqlite", rates.SCHEMA)
    offers, _ = rates.parse_offers(products)
    check_in, check_out = date(2027, 9, 20), date(2027, 9, 24)

    first, second = datetime(2026, 11, 1, tzinfo=UTC), datetime(2026, 11, 2, tzinfo=UTC)
    rates.save(db, "BOBWI", check_in, check_out, 2, offers, scanned_at=first)
    cheaper = [
        replace(o, total=700000.0) if o.rate_code == "ECPZ" else o for o in offers
    ]
    rates.save(db, "BOBWI", check_in, check_out, 2, cheaper, scanned_at=second)

    days = [check_in, date(2027, 9, 21)]
    best = rates.best_per_date(
        db, "BOBWI", days, 4, 2, room="Lagoon View", rate="Half Board"
    )
    assert best[0].offer.total == 700000.0
    assert best[1].offer is None

    overall = rates.best_per_date(db, "BOBWI", days, 4, 2)
    assert overall[0].offer.rate_code == "AP7D"


def test_price_changes(products, tmp_path):
    db = store.open_db(tmp_path / "t.sqlite", rates.SCHEMA)
    offers, _ = rates.parse_offers(products)
    check_in, check_out = date(2027, 9, 20), date(2027, 9, 24)
    first, second = datetime(2026, 11, 1, tzinfo=UTC), datetime(2026, 11, 8, tzinfo=UTC)
    rates.save(db, "BOBWI", check_in, check_out, 2, offers, scanned_at=first)
    # a date scanned only once
    rates.save(
        db, "BOBWI", date(2027, 9, 21), date(2027, 9, 25), 2, offers, scanned_at=first
    )

    later = []
    for o in offers:
        if o.rate_code == "ECPZ":
            later.append(replace(o, total=o.total * 0.95))  # -5%
        elif o.rate_code == "AP7D":
            later.append(replace(o, total=o.total * 1.01))  # +1%, below threshold
        elif o.rate_code != "SNLC":  # SNLC gone
            later.append(o)
    later.append(
        replace(offers[0], room_name="Royal Overwater w/Pool", rate_code="NEW1")
    )
    rates.save(db, "BOBWI", check_in, check_out, 2, later, scanned_at=second)

    result = rates.price_changes(db, "BOBWI", date.min, date.max, 4, 2)
    assert (result.compared, result.single) == (1, 1)
    by_code = {c.rate_code: c for c in result.changes}
    assert set(by_code) == {"ECPZ", "SNLC", "NEW1"}
    assert by_code["ECPZ"].before == 811507 and round(by_code["ECPZ"].pct, 1) == -5.0
    assert by_code["SNLC"].after is None and by_code["SNLC"].pct is None
    assert by_code["NEW1"].before is None

    filtered = rates.price_changes(
        db, "BOBWI", date.min, date.max, 4, 2, rate="Half Board"
    )
    assert [c.rate_code for c in filtered.changes] == ["ECPZ"]
    assert {
        c.rate_code
        for c in rates.price_changes(
            db, "BOBWI", date.min, date.max, 4, 2, min_pct=0.5
        ).changes
    } >= {"AP7D"}
    assert "LP5F" not in {
        c.rate_code
        for c in rates.price_changes(
            db, "BOBWI", date.min, date.max, 4, 2, min_pct=0
        ).changes
    }
    assert rates.price_changes(db, "BOBWI", date.min, date.max, 5, 2).compared == 0
