import logging
from datetime import datetime
from json import dumps

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from uvicorn import run

from play.auth import require_user
from play.config import get_settings
from play.digest.build import get_digest
from play.energy.spot import spot_chart
from play.energy.water import meter_snapshot
from play.mail import send_email
from play.templating import templates

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="play")


@app.exception_handler(httpx.HTTPError)
async def upstream_error(request: Request, exc: httpx.HTTPError):
    log.error("upstream error on %s: %r", request.url.path, exc)
    return JSONResponse({"detail": f"upstream error: {exc}"}, status_code=502)


@app.get("/")
async def root(request: Request):
    payload = {
        "message": "server is up",
        "paths": [
            "/view",
            "/public/spot",
            "/public/water.jpg",
            "POST /scheduled?audience=N",
        ],
    }
    if "text/html" not in request.headers.get("accept", "").lower():
        return JSONResponse(payload)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Server is up",
            "payload": dumps(payload, indent=2),
            "redirect_url": "https://yan.fi",
            "delay": 10,
        },
    )


@app.get("/public/spot", response_class=HTMLResponse)
async def spot():
    return await spot_chart.html(datetime.now(get_settings().zone))


@app.get(
    "/public/water.jpg",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}},
)
async def water_jpg():
    return Response(content=await meter_snapshot(), media_type="image/jpeg")


@app.get("/view", response_class=HTMLResponse)
async def view(_: str = Depends(require_user)):
    return (await get_digest()).html


@app.post("/scheduled")
async def scheduled(audience: int = 1, _: str = Depends(require_user)):
    """Rebuild the digest and email it to the first `audience` recipients (0 = refresh only)."""
    digest = await get_digest(refresh=True)
    recipients = get_settings().email_recipients[: max(audience, 0)]
    if recipients:
        await send_email(digest.title, digest.html, recipients)
    return {"title": digest.title, "sent_to": len(recipients)}


def main():
    run(app, host="0.0.0.0", port=7999)


def main_dev():
    run("play.main:app", host="0.0.0.0", port=7999, reload=True)
