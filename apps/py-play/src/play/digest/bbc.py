"""BBC football fixtures from the JSON API behind bbc.com/sport/football/scores-fixtures."""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

from play.httpclient import client

log = logging.getLogger(__name__)

PAGE_URL = "https://www.bbc.com/sport/football/scores-fixtures"
API_URL = (
    "https://web-cdn.api.bbci.co.uk/wc-poll-data/container/sport-data-scores-fixtures"
)
COLLECTION_URN = "urn:bbc:sportsdata:football:tournament-collection:collated"


@dataclass(frozen=True)
class Game:
    time: str  # local kickoff, or BBC status once started (FT, 67', Postponed)
    home: str
    away: str
    score: str | None = None


async def fetch_fixtures(day: date) -> dict:
    params = {
        "selectedStartDate": day.isoformat(),
        "selectedEndDate": day.isoformat(),
        "todayDate": day.isoformat(),
        "urn": COLLECTION_URN,
    }
    async with client() as c:
        r = await c.get(API_URL, params=params)
        r.raise_for_status()
        return r.json()


def parse_fixtures(data: dict, zone: ZoneInfo) -> dict[str, list[Game]]:
    """Competition name -> games, in BBC's order."""
    out: dict[str, list[Game]] = {}
    for group in data.get("eventGroups", []):
        games = [
            game
            for sub in group.get("secondaryGroups", [])
            for event in sub.get("events", [])
            if (game := _parse_event(event, zone))
        ]
        if games:
            out.setdefault(group.get("displayLabel") or "Other", []).extend(games)
    return out


def _parse_event(event: dict, zone: ZoneInfo) -> Game | None:
    try:
        home, away = event["home"], event["away"]
        if event.get("status") == "PreEvent":
            start = datetime.fromisoformat(event["startDateTime"])
            time = f"{start.astimezone(zone):%H:%M}"
        else:
            time = (event.get("statusComment") or {}).get("value", "")
        score = (
            f"{home['score']}-{away['score']}"
            if "score" in home and "score" in away
            else None
        )
        return Game(
            time=time, home=home["fullName"], away=away["fullName"], score=score
        )
    except (KeyError, TypeError, ValueError) as e:
        log.warning("skipping BBC event %s: %r", event.get("id"), e)
        return None


async def get_fixtures(day: date, zone: ZoneInfo) -> dict[str, list[Game]]:
    return parse_fixtures(await fetch_fixtures(day), zone)
