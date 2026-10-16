"""Daily digest (football fixtures + HOK-Elanto Bonus tuplana) for /view and the morning email."""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from hashlib import md5

from play.config import get_settings
from play.digest import bbc, hok
from play.templating import templates

log = logging.getLogger(__name__)

EXCLUDED = re.compile(
    r"league one|league two|national league|fa trophy|efl trophy|scottish cup|lowland",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Digest:
    title: str
    html: str


_latest: Digest | None = None


async def get_digest(refresh: bool = False) -> Digest:
    global _latest
    if refresh or _latest is None:
        _latest = await build_digest()
    return _latest


async def build_digest() -> Digest:
    zone = get_settings().zone
    now = datetime.now(zone)
    fixtures, campaigns = await asyncio.gather(
        bbc.get_fixtures(now.date(), zone), hok.get_campaigns(), return_exceptions=True
    )
    if isinstance(fixtures, BaseException):
        raise fixtures
    bonus_error = None
    if isinstance(campaigns, BaseException):
        log.warning("HOK-Elanto failed: %r", campaigns)
        campaigns, bonus_error = [], f"failed to load content: {campaigns!r}"
    return render_digest(fixtures, campaigns, now, bonus_error)


def render_digest(
    fixtures: dict[str, list[bbc.Game]],
    campaigns: list[str],
    now: datetime,
    bonus_error: str | None = None,
) -> Digest:
    competitions = [
        {"name": name, "games": games, "color": _color(name)}
        for name, games in fixtures.items()
        if not EXCLUDED.search(name)
    ]
    title = (
        ", ".join(f"{len(c['games'])} {c['name']}" for c in competitions[:2])
        or "No fixtures"
    )
    if campaigns:
        title = f"BonusX2 {title}"
    html = templates.get_template("digest.html").render(
        competitions=competitions,
        campaigns=campaigns,
        bonus_error=bonus_error,
        updated=now,
        bbc_url=bbc.PAGE_URL,
        hok_url=hok.PAGE_URL,
    )
    return Digest(title=title, html=html)


def _color(name: str) -> str:
    return "#" + md5(name.encode()).hexdigest()[:6]  # stable per competition
