"""Migri estimated processing time for adult citizenship (electronic); the page is server-rendered."""

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from play.httpclient import client

PAGE_URL = "https://migri.fi/en/processing-times"
SECTION = "Citizenship application for an adult"
COLUMN = "Electronic application"


@dataclass(frozen=True)
class ProcessingTime:
    most: str  # "in most cases", as published, e.g. "35 months" or "9–31 months"
    minority: str  # "in a minority of cases"


async def fetch_page() -> str:
    async with client() as c:
        r = await c.get(PAGE_URL)
        r.raise_for_status()
        return r.text


def parse_processing_time(html: str) -> ProcessingTime:
    soup = BeautifulSoup(html, "html.parser")
    for heading in soup.select(".tabPanel .heading"):
        if _norm(heading.get_text()).lower() != SECTION.lower():
            continue
        table = heading.find_parent(class_="tabPanel").find("table")
        rows = [
            [_norm(cell.get_text(" ")) for cell in tr.find_all(["td", "th"])]
            for tr in table.find_all("tr")
        ]
        header = [h.lower() for h in rows[0]]
        if COLUMN.lower() not in header:
            raise ValueError(f"{COLUMN!r} column not found")
        col = header.index(COLUMN.lower())
        values = {r[0].lower(): r[col] for r in rows[1:] if len(r) > col}
        return ProcessingTime(
            most=_value(values, "in most cases"),
            minority=_value(values, "in a minority of cases"),
        )
    raise ValueError(f"{SECTION!r} not found")


async def get_processing_time() -> ProcessingTime:
    return parse_processing_time(await fetch_page())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _value(values: dict[str, str], row: str) -> str:
    for label, value in values.items():
        if label.endswith(row) and value:
            return value
    raise ValueError(f"{row!r} row not found")
