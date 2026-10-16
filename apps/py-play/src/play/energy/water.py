"""Water meter crop from Frigate's `tech` camera snapshot."""

import asyncio
from io import BytesIO

from PIL import Image

from play.config import get_settings
from play.httpclient import client

TRIM_W, TRIM_H = 0.31, 0.6  # meter is in the top-left of the frame


async def meter_snapshot() -> bytes:
    async with client() as c:
        r = await c.get(f"{get_settings().frigate_url}/api/tech/latest.jpg")
        r.raise_for_status()
    return await asyncio.to_thread(crop_meter, r.content)


def crop_meter(jpeg: bytes) -> bytes:
    with Image.open(BytesIO(jpeg)) as img:
        w, h = img.size
        meter = img.crop((0, 0, int(w * TRIM_W), int(h * TRIM_H))).transpose(
            Image.Transpose.ROTATE_90
        )
    out = BytesIO()
    meter.save(out, "JPEG", quality=95)
    return out.getvalue()
