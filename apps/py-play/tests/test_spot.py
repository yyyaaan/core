import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from play.energy import spot
from play.energy.spot import Price, SpotChart, current_price, render_chart

TZ = ZoneInfo("Europe/Helsinki")
MIDNIGHT = datetime(2026, 10, 16, tzinfo=TZ)


def day_prices(days=1):
    return [Price(MIDNIGHT + i * spot.QUARTER, i / 10) for i in range(96 * days)]


def test_current_price_is_the_running_quarter():
    assert (
        current_price(day_prices(), MIDNIGHT + timedelta(hours=10, minutes=20)).cent
        == 4.1
    )


def test_render_chart_title():
    html = render_chart(day_prices(), MIDNIGHT + timedelta(hours=10, minutes=20))
    assert "Nordpool Finland: 4.1" in html


@pytest.fixture
def fetches(monkeypatch):
    calls = []

    async def fake(now):
        calls.append(now)
        return day_prices(2 if now.hour >= spot.TOMORROW_AFTER_HOUR else 1)

    monkeypatch.setattr(spot, "fetch_prices", fake)
    return calls


def test_refetches_for_tomorrow_after_publication(fetches):
    chart = SpotChart()
    asyncio.run(chart.html(MIDNIGHT + timedelta(hours=9)))
    asyncio.run(chart.html(MIDNIGHT + timedelta(hours=13)))
    assert len(fetches) == 1  # today complete, too early for tomorrow
    asyncio.run(chart.html(MIDNIGHT + timedelta(hours=14)))
    asyncio.run(chart.html(MIDNIGHT + timedelta(hours=16)))
    assert len(fetches) == 2


def test_serves_cached_prices_when_refresh_fails(fetches, monkeypatch):
    chart = SpotChart()
    asyncio.run(chart.html(MIDNIGHT + timedelta(hours=9)))

    async def down(now):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(spot, "fetch_prices", down)
    assert "Nordpool Finland" in asyncio.run(chart.html(MIDNIGHT + timedelta(hours=15)))
    assert chart.fetched_at == MIDNIGHT + timedelta(hours=15)  # retry throttled
    with pytest.raises(httpx.ConnectError):
        asyncio.run(SpotChart().html(MIDNIGHT))
