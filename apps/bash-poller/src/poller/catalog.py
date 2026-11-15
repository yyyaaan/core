"""Rebuild the public timelapse catalog in R2 from what is actually there.

Writes timelapse/index.json (consumed by the viewer and Home Assistant)
and timelapse/index.html (the viewer, timelapse.html next to this file).
A YYYYMMDD_lite.mp4 / YYYYMM_lite.mp4 sibling is listed as the entry's `lite` copy.

python /app/catalog.py
"""

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

from upload import r2_client

PREFIX = "timelapse/"
PATTERNS = {
    "daily": re.compile(r"timelapse/daily/(\d{4})(\d{2})(\d{2})(_lite)?\.mp4"),
    "monthly": re.compile(r"timelapse/monthly/(\d{4})(\d{2})(_lite)?\.mp4"),
}
VIEWER = Path(__file__).with_name("timelapse.html")
CACHE = "public, max-age=300"  # short, so Cloudflare's edge doesn't serve a stale list


def build_catalog(objects: list[dict], base_url: str) -> dict:
    """objects: list_objects_v2 entries (Key, Size). Newest first per kind."""

    def item(o: dict) -> dict:
        return {
            "key": o["Key"],
            "url": base_url + o["Key"],
            "size_mb": round(o["Size"] / 1e6, 1),
        }

    catalog = {"updated": datetime.now(UTC).isoformat(timespec="seconds")}
    for kind, pattern in PATTERNS.items():
        full, lite = {}, {}
        for o in objects:
            if m := pattern.fullmatch(o["Key"]):
                *date, is_lite = m.groups()
                (lite if is_lite else full)["-".join(date)] = o  # YYYY-MM-DD or YYYY-MM
        entries = []
        for date, o in full.items():  # a lite copy without its full one is not listed
            entry = {"date": date, **item(o)}
            if date in lite:
                entry["lite"] = item(lite[date])
            entries.append(entry)
        catalog[kind] = sorted(entries, key=lambda e: e["date"], reverse=True)
    return catalog


def main() -> None:
    s3, bucket = r2_client()
    base_url = os.environ.get("R2_PUBLIC_URL", "").rstrip("/") + "/"
    pages = s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=PREFIX)
    objects = [o for page in pages for o in page.get("Contents", [])]
    catalog = build_catalog(objects, base_url)

    s3.put_object(
        Bucket=bucket,
        Key=PREFIX + "index.json",
        Body=json.dumps(catalog, indent=1).encode(),
        ContentType="application/json",
        CacheControl=CACHE,
    )
    s3.put_object(
        Bucket=bucket,
        Key=PREFIX + "index.html",
        Body=VIEWER.read_bytes(),
        ContentType="text/html; charset=utf-8",
        CacheControl=CACHE,
    )
    print(
        f"Catalog: {len(catalog['daily'])} daily, {len(catalog['monthly'])} monthly"
        f" -> {base_url}{PREFIX}index.html"
    )


if __name__ == "__main__":
    main()
