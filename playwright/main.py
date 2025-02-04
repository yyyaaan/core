"""
docker build -t playwright:macos .
docker run -it --rm -v ./:/home/appuser/src -p 7999:7999 --entrypoint bash playwright:macos
uvicorn main:app --port 7999 --host 0.0.0.0 --reload
docker build --platform=linux/amd64 -t playwright:release .
docker tag playwright:release yyyaaan/playright:v0.4.7
"""
from datetime import datetime, UTC
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from os import getenv
from uvicorn import run

from play.html import sports_and_bonus
from utils.SendGrid import SendGrid
from utils.ViewLogs import ViewLogs
from energy.WaterMeter import WaterMeter
from energy.Electricity import Electricity

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "server is up", "paths": ["/view", "/scheduled&audience=0", "now"]}


@app.get("/logs")
async def logs(filename: str = ""):
    return HTMLResponse(content=ViewLogs.view_logs(filename))


@app.get("/spot")
async def spot():
    return HTMLResponse(content=Electricity().get_current_plot())


@app.get("/water.jpg", responses={200: {"content": {"image/jpeg": {}}}})
async def water_jpg():
    return Response(
        content=WaterMeter().get_snapshot_content(),
        media_type="image/jpeg"
    )


@app.get("/view")
def view():
    return HTMLResponse(content=sports_and_bonus(refresh=False)["html"])


@app.post("/scheduled")
def scheduled(request: Request):
    """
    Scheduled tasks. Optional query parameter: now, audience
    """
    params = request.query_params
    the_hour = datetime.now(UTC).hour
    hour_bbc = the_hour if "now" in params else getenv("HOUR_BBC", "7")
    try:
        n_audience = int(params.get("audience", ""))
    except Exception:
        n_audience = 1

    if str(the_hour) == str(hour_bbc):
        payload = sports_and_bonus(refresh=True)
        SendGrid().send_email(
            subject=payload["title"],
            content=payload["html"],
            audience_length=abs(n_audience),
        )

    print(f"the_hour: {the_hour}, hour_bbc: {hour_bbc}, params: {params}")
    return {
        "hour": the_hour,
        "bbc": hour_bbc,
    }


if __name__ == '__main__':
    run(app, host="0.0.0.0", port=7999)

# curl -X POST https://pi.yan.fi/play/scheduled?audience=1&now=true