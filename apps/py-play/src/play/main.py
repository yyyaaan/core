"""
docker build -t playwright:macos .
docker run -it --rm -v ./:/home/appuser/src -p 7999:7999 --entrypoint bash playwright:macos
uvicorn main:app --port 7999 --host 0.0.0.0 --reload
docker build --platform=linux/amd64 -t playwright:release .
docker tag playwright:release yyyaaan/playright:v0.5.0
"""

from datetime import datetime
from glob import glob
from os import getenv

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from energy.Electricity import Electricity
from energy.WaterMeter import WaterMeter
from play.html import sports_and_bonus
from utils.EmailClient import EmailClient
from utils.ViewLogs import ViewLogs
from pytz import timezone
from uvicorn import run

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": "server is up",
        "paths": ["/view", "/scheduled&audience=0", "now"],
    }


@app.get("/logs")
async def logs(filename: str = ""):
    return HTMLResponse(content=ViewLogs.view_logs(filename))


@app.get("/public/spot")
async def spot():
    return HTMLResponse(content=Electricity().get_current_plot())


@app.get("/public/water.jpg", responses={200: {"content": {"image/jpeg": {}}}})
async def water_jpg():
    return Response(
        content=WaterMeter().get_snapshot_content(), media_type="image/jpeg"
    )


@app.get("/markdown", response_class=HTMLResponse)
async def html_render_markdown(
    request: Request,
    title: str = "Minimal Page",
    file_name: str = "base.md",
    style_name: str = "base.css",
):
    folder = "/mnt/md"
    try:
        with open(f"{folder}/{file_name}", "r", encoding="utf8") as f:
            markdown_content = f.read()
        with open(f"{folder}/{style_name}", "r", encoding="utf8") as f:
            style_content = f.read()
    except Exception as e:
        markdown_content = f"## Error details: {e}"
        markdown_content += (
            "\n\n"
            + ", ".join([
                "`" + x.replace("{folder}/base_", "").replace(".md", "") + "`"
                for x in glob("{folder}/*.md")
            ])
            + "\n"
        )
        style_content = ""

    return Jinja2Templates(directory="templates/").TemplateResponse(
        request=request,
        name="minimal.html",
        context={
            "request": request,
            "title": title,
            "rendered_markdown": markdown(markdown_content),
            "style_content": style_content,
        },
    )


@app.get("/view")
async def view():
    content = await sports_and_bonus(refresh=False)
    return HTMLResponse(content=content["html"])


@app.post("/scheduled")
async def scheduled(request: Request):
    """
    Scheduled tasks. Optional query parameter: now, audience
    """
    params = request.query_params
    the_hour = datetime.now(timezone("Europe/Helsinki")).hour
    hour_bbc = the_hour if "now" in params else getenv("HOUR_BBC", "9")
    try:
        n_audience = int(params.get("audience", ""))
    except Exception:
        n_audience = 1

    if str(the_hour) == str(hour_bbc):
        payload = await sports_and_bonus(refresh=True)
        EmailClient().send_email(
            subject=payload["title"],
            content=payload["html"],
            audience_length=abs(n_audience),
        )

    print(f"the_hour: {the_hour}, hour_bbc: {hour_bbc}, params: {params}")
    return {
        "hour": the_hour,
        "bbc": hour_bbc,
    }


def main():
    run(app, host="0.0.0.0", port=7999)


if __name__ == "__main__":
    main()

# curl -X POST https://pi.yan.fi/play/scheduled?audience=1&now=true
