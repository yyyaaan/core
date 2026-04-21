import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Get directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()

# Setup Templates (Jinja2)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mock data
projects = [
    {
        "id": "resonant",
        "title": "Resonant",
        "desc": "AI-native exploration interface.",
        "color": "#F27D26",
    },
    {
        "id": "ditto",
        "title": "Ditto",
        "desc": "Collaborative design workspace.",
        "color": "#00FF00",
    },
    {
        "id": "utility",
        "title": "Utility",
        "desc": "Technical instrumentation suite.",
        "color": "#3B82F6",
    },
    {
        "id": "flex",
        "title": "Flex",
        "desc": "Dynamic branding system.",
        "color": "#EF4444",
    },
    {
        "id": "ditto-2",
        "title": "Ditto",
        "desc": "Collaborative design workspace.",
        "color": "#8B5CF6",
    },
    {
        "id": "utility-2",
        "title": "Utility",
        "desc": "Technical instrumentation suite.",
        "color": "#EC4899",
    },
]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"projects": projects})


@app.get("/api/contact", response_class=HTMLResponse)
async def get_contact(request: Request):
    return templates.TemplateResponse(request, "partials/contact.html")


@app.get("/api/project/{project_id}", response_class=HTMLResponse)
async def get_project(request: Request, project_id: str):
    project = next((p for p in projects if p["id"] == project_id), None)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Return the HTML fragment for HTMX
    return templates.TemplateResponse(
        request, "partials/project_detail.html", {"project": project}
    )


def main():
    uvicorn.run(app, host="0.0.0.0", port=8001)


def main_dev():
    uvicorn.run("web.main:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    main()
