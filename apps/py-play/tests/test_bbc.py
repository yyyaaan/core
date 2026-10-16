import json
from zoneinfo import ZoneInfo

import pytest

from play.digest.bbc import Game, parse_fixtures

HELSINKI = ZoneInfo("Europe/Helsinki")


@pytest.fixture
def parsed(fixture_text):
    return parse_fixtures(json.loads(fixture_text("bbc_fixtures.json")), HELSINKI)


def test_groups_keep_bbc_order_and_merge_subgroups(parsed):
    out = parsed
    assert list(out) == [
        "Championship",
        "Highland / Lowland",
        "Welsh Cup",
        "CONMEBOL Libertadores",
    ]
    assert [g.home for g in out["Highland / Lowland"]] == [
        "Strathspey Thistle",
        "Celtic II",
    ]


def test_event_states(parsed):
    out = parsed
    assert out["Welsh Cup"][0] == Game(
        time="21:30", home="Evans & Williams", away="Rockspur"
    )  # 18:30Z in EEST
    assert out["Championship"] == [
        Game(time="21'", home="Burnley", away="Wolverhampton Wanderers", score="1-0")
    ]
    assert out["CONMEBOL Libertadores"][0].time == "FT"
    assert out["CONMEBOL Libertadores"][0].score == "0-0"


def test_malformed_event_is_skipped_not_fatal(parsed):
    assert len(parsed["Championship"]) == 1
