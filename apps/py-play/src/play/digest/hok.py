"""HOK-Elanto "Bonus tuplana" (double S-Bonus) campaigns; the page is server-rendered."""

from bs4 import BeautifulSoup

from play.httpclient import client

PAGE_URL = "https://hok-elanto.fi/s-etukortti/ajankohtaista-asiakasomistajalle"


async def fetch_page() -> str:
    async with client(timeout=12) as c:
        r = await c.get(PAGE_URL)
        r.raise_for_status()
        return r.text


def parse_campaigns(html: str) -> list[str]:
    """Active campaigns; [] when none. Raises if the section itself is gone."""
    soup = BeautifulSoup(html, "html.parser")
    for article in soup.find_all("article"):
        heading = article.find("h2")
        if not heading or "tuplana" not in heading.get_text().lower():
            continue
        # editors list campaigns either as <li> items or as "- ..." lines in spans
        lines = [li.get_text(" ", strip=True) for li in article.find_all("li")]
        lines += [
            line
            for span in article.find_all("span")
            for line in span.get_text().splitlines()
            if line.strip().startswith("-")
        ]
        campaigns = []
        for line in lines:
            line = line.strip().lstrip("-–").strip()
            if (
                len(line) > 5
                and "ei kampanjoita" not in line.lower()
                and line not in campaigns
            ):
                campaigns.append(line)
        return campaigns
    raise ValueError("Bonus tuplana section not found")


async def get_campaigns() -> list[str]:
    return parse_campaigns(await fetch_page())
