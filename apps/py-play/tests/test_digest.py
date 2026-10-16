import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from play.digest import bbc, build, hok
from play.digest.bbc import Game

NOW = datetime(2026, 10, 17, 9, 39, tzinfo=ZoneInfo("Europe/Helsinki"))
FIXTURES = {
    "Premier League": [
        Game("14:30", "Everton", "Chelsea"),
        Game("17:00", "Brentford", "Liverpool"),
    ],
    "League One": [Game("14:30", "MK Dons", "Luton Town")],
    "Welsh Cup": [Game("16:00", "Evans & Williams", "Rockspur")],
}


def test_render_excludes_and_titles():
    d = build.render_digest(FIXTURES, [], NOW)
    assert d.title == "2 Premier League, 1 Welsh Cup"
    assert "MK Dons" not in d.html
    assert "Evans &amp; Williams" in d.html
    assert "HOK-Elanto no offer available" in d.html
    assert "Oct 17 09:39:00 EEST" in d.html


def test_render_with_campaign():
    d = build.render_digest(FIXTURES, ["Prisma Itäkeskus 11.-17.5."], NOW)
    assert d.title.startswith("BonusX2 ")
    assert "- Prisma Itäkeskus 11.-17.5." in d.html


def test_hok_failure_is_soft(monkeypatch):
    async def fixtures(day, zone):
        return FIXTURES

    async def boom():
        raise ValueError("Bonus tuplana section not found")

    monkeypatch.setattr(bbc, "get_fixtures", fixtures)
    monkeypatch.setattr(hok, "get_campaigns", boom)
    d = asyncio.run(build.build_digest())
    assert "failed to load content" in d.html


def test_bbc_failure_raises(monkeypatch):
    async def boom(day, zone):
        raise RuntimeError("bbc down")

    async def campaigns():
        return []

    monkeypatch.setattr(bbc, "get_fixtures", boom)
    monkeypatch.setattr(hok, "get_campaigns", campaigns)
    with pytest.raises(RuntimeError):
        asyncio.run(build.build_digest())
