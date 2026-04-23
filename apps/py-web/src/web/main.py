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

with open(os.path.join(BASE_DIR, "static", "yan.jpg.txt"), "r") as f:
    yan_image_base64 = f.read().strip()

# Mock data
projects = [
    {
        "id": "about",
        "title": "About Me",
        "context": "Human / Engineer",
        "summary": "System Architect<br/>CV & Background",
        "desc": "A comprehensive look at my professional journey, education, and technical stack.",
        "color": "#6ae5ee",
        "icon": "user",
        "image": f"data:image/jpeg;base64,{yan_image_base64}",
        "isAbout": True,
    },
    {
        "id": "omop",
        "title": "OMOP CDM",
        "context": "Healthcare Engineering",
        "summary": "Healthcare Data ETL<br/>OHDSI Ecosystem Cloud",
        "desc": "Individual contributor to OHDSI/OMOP CDM ETL pipelines. Transforming healthcare data into standard formats.",
        "color": "#10B981",
        "icon": "activity",
        "image": "https://images.unsplash.com/photo-1504813184591-01f944cdf0f4?q=80&w=800&auto=format&fit=crop",
    },
    {
        "id": "kubernetes",
        "title": "K8s Cluster",
        "context": "GitOps Orchestration",
        "summary": "ArgoCD / GitOps / K3s<br/>Prometheus + Grafana",
        "desc": "Technical instrumentation suite for distributed systems.",
        "color": "#3B82F6",
        "icon": "server",
        "image": "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?q=80&w=800&auto=format&fit=crop",
    },
    {
        "id": "home",
        "title": "Smart Home",
        "context": "Home Automation",
        "summary": "Home Assistant<br/>K8s Integration",
        "desc": "Powering smart homes with Home Assistant, Frigate, and HomeBridge running on Kubernetes.",
        "color": "#8B5CF6",
        "icon": "home",
        "image": "https://images.unsplash.com/photo-1558002038-1055907df827?q=80&w=800&auto=format&fit=crop",
    },
    {
        "id": "ai_ml",
        "title": "AI/ML Prof.",
        "context": "Applied Intel",
        "summary": "Advanced ML Pipelines<br/>Neural Architecture",
        "desc": "Developing production-grade AI/ML pipelines, focusing on transformer architectures and high-performance inference systems.",
        "color": "#EF4444",
        "icon": "brain",
        "image": "https://images.unsplash.com/photo-1677442136019-21780ecad995?q=80&w=800&auto=format&fit=crop",
    },
    {
        "id": "utility",
        "title": "Utility",
        "context": "System Nodes",
        "summary": "Technical Suite<br/>Instrumentation",
        "desc": "Direct access to internal infrastructure dashboards and micro-services.",
        "color": "#EC4899",
        "icon": "cpu",
        "image": "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop",
        "sublinks": [
            {"label": "Dash", "url": "https://dash.yan.fi"},
            {"label": "ArgoCD", "url": "https://argocd.yan.fi"},
            {"label": "Home", "url": "https://h.yan.fi"},
            {"label": "Frigate", "url": "https://frigate.yan.fi"},
            {"label": "Bridge", "url": "https://homebridge.yan.fi"},
        ],
    },
]


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"projects": projects})


@app.get("/public/api/contact", response_class=HTMLResponse)
async def get_contact(request: Request):
    return templates.TemplateResponse(request, "partials/contact.html")


@app.get("/public/api/project/{project_id}", response_class=HTMLResponse)
async def get_project(request: Request, project_id: str):
    if project_id == "about":
        return templates.TemplateResponse(request, "partials/about_cv.html")

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
