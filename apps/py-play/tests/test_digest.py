import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from play.digest import bbc, build, hok, migri
from play.digest.bbc import Game
from play.digest.migri import ProcessingTime

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
    assert "Migri processing time unavailable." in d.html


def test_render_with_processing_time():
    d = build.render_digest(
        FIXTURES, [], NOW, processing_time=ProcessingTime("35 months", "17 months")
    )
    assert (
        "Migri adult citizenship (electronic): 35 months in most cases, 17 months in a minority of cases."
        in d.html
    )
    assert "12 months" not in d.html


def test_render_with_campaign():
    d = build.render_digest(FIXTURES, ["Prisma Itäkeskus 11.-17.5."], NOW)
    assert d.title.startswith("BonusX2 ")
    assert "- Prisma Itäkeskus 11.-17.5." in d.html


async def _fixtures(day, zone):
    return FIXTURES


async def _no_campaigns():
    return []


async def _processing_time():
    return ProcessingTime("35 months", "17 months")


def test_hok_and_migri_failures_are_soft(monkeypatch):
    async def boom():
        raise ValueError("section not found")

    monkeypatch.setattr(bbc, "get_fixtures", _fixtures)
    monkeypatch.setattr(hok, "get_campaigns", boom)
    monkeypatch.setattr(migri, "get_processing_time", boom)
    d = asyncio.run(build.build_digest())
    assert "failed to load content" in d.html
    assert "Migri processing time unavailable." in d.html
    assert "Premier League" in d.html


def test_build_includes_processing_time(monkeypatch):
    monkeypatch.setattr(bbc, "get_fixtures", _fixtures)
    monkeypatch.setattr(hok, "get_campaigns", _no_campaigns)
    monkeypatch.setattr(migri, "get_processing_time", _processing_time)
    assert "35 months in most cases" in asyncio.run(build.build_digest()).html


def test_bbc_failure_raises(monkeypatch):
    async def boom(day, zone):
        raise RuntimeError("bbc down")

    monkeypatch.setattr(bbc, "get_fixtures", boom)
    monkeypatch.setattr(hok, "get_campaigns", _no_campaigns)
    monkeypatch.setattr(migri, "get_processing_time", _processing_time)
    with pytest.raises(RuntimeError):
        asyncio.run(build.build_digest())
