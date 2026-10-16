"""Nordpool FI spot prices (15-min resolution, via Elering) as a Plotly bar chart."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

import httpx
import plotly.graph_objects as go

from play.httpclient import client

log = logging.getLogger(__name__)

API_URL = "https://dashboard.elering.ee/api/nps/price"
VAT = 1.255
REFERENCE_CENT = 8.96  # dashed reference line
QUARTER = timedelta(minutes=15)
TOMORROW_AFTER_HOUR = 14  # day-ahead prices land ~13:45 Finnish time
COLOR_NOW, COLOR = "#a291e1", "#c2d0e9"


@dataclass(frozen=True)
class Price:
    start: datetime
    cent: float  # c/kWh incl. VAT


async def fetch_prices(now: datetime) -> list[Price]:
    """Today and tomorrow (local), whatever is published."""
    start = datetime.combine(now.date(), time(), now.tzinfo)
    end = start + timedelta(days=2)
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    params = {
        "start": f"{start.astimezone(UTC):{fmt}}",
        "end": f"{end.astimezone(UTC):{fmt}}",
    }
    async with client() as c:
        r = await c.get(API_URL, params=params)
        r.raise_for_status()
    rows = r.json().get("data", {}).get("fi", [])
    prices = [
        Price(
            datetime.fromtimestamp(x["timestamp"], now.tzinfo),
            round(x["price"] * VAT / 10, 2),
        )
        for x in rows
    ]
    return [p for p in prices if start <= p.start < end]  # API end bound is inclusive


def current_price(prices: list[Price], now: datetime) -> Price | None:
    return next((p for p in prices if p.start <= now < p.start + QUARTER), None)


def render_chart(prices: list[Price], now: datetime) -> str:
    current = current_price(prices, now)
    title = (
        f"Nordpool Finland: {current.cent} €ent/kWh"
        if current
        else "Nordpool Finland: no current price"
    )
    # naive local times: plotly.js shows wall-clock time as given
    fig = go.Figure(
        go.Bar(
            x=[p.start.replace(tzinfo=None) for p in prices],
            y=[p.cent for p in prices],
            marker_color=[COLOR_NOW if p is current else COLOR for p in prices],
            hovertemplate="%{x|%a %H:%M} %{y:.2f} c<extra></extra>",
        )
    )
    fig.add_hline(y=REFERENCE_CENT, line_dash="dash", line_color=COLOR_NOW)
    midnight = datetime.combine(now.date() + timedelta(days=1), time())
    fig.add_vline(x=midnight.isoformat(), line_width=1, line_color="#ccc")
    fig.update_layout(
        title=title,
        title_font_size=15,
        bargap=0.1,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0),
    )
    fig.update_xaxes(tickformat="%H", dtick=3 * 3600 * 1000)
    return fig.to_html(
        full_html=True, include_plotlyjs=True, config={"displayModeBar": False}
    )


class SpotChart:
    """Caches prices (refetching when incomplete) and the chart per quarter-hour."""

    def __init__(self):
        self.prices: list[Price] = []
        self.fetched_at: datetime | None = None
        self.rendered: tuple[datetime, str] | None = None

    async def html(self, now: datetime) -> str:
        if self._stale(now):
            try:
                self.prices = await fetch_prices(now)
                self.fetched_at, self.rendered = now, None
            except httpx.HTTPError:
                if not self.prices:
                    raise
                log.exception("Elering refresh failed, serving cached prices")
        quarter = now.replace(minute=now.minute // 15 * 15, second=0, microsecond=0)
        if not self.rendered or self.rendered[0] != quarter:
            self.rendered = (quarter, render_chart(self.prices, now))
        return self.rendered[1]

    def _stale(self, now: datetime) -> bool:
        if self.fetched_at is None:
            return True
        if now - self.fetched_at < QUARTER:
            return False
        tomorrow = now.date() + timedelta(days=1)
        has_tomorrow = any(p.start.date() == tomorrow for p in self.prices)
        return not current_price(self.prices, now) or (
            now.hour >= TOMORROW_AFTER_HOUR and not has_tomorrow
        )


spot_chart = SpotChart()
