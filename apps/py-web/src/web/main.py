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
        "id": "kubernetes",
        "title": "Kubernetes Cluster",
        "summary": "Technical Instrumentation Suite<br/>ArgoCD for GitOpsContinuous Delivery<br/>Headlamp for Observability<br/>Prometheus + Grafana for Metrics",
        "desc": "Technical instrumentation suite.",
        "color": "#3B82F6",
    },
    {
        "id": "omop",
        "title": "OMOP",
        "summary": "OHDSI/OMOP CDM ETL pipelines.<br/>OMOP Ecosystem Cloud Engineering.",
        "desc": "Individual contributor to the OHDSI/OMOP CDM ETL pipelines. Developed and maintained robust ETL pipelines to transform healthcare data into the OMOP Common Data Model (CDM) format, ensuring data consistency and quality for research and analysis.",
        "color": "#00FF00",
    },
    {
        "id": "resonant",
        "title": "Resonant",
        "summary": "Resonant Archives<br/>Web Scrapping<br/>R, Shiny, Data Visualization<br/>R & SAS in clinical research",
        "desc": "Clinical Research Data Analysis and Visualization. Utilized R and SAS for data analysis in clinical research projects, including data cleaning, statistical analysis, and visualization. Developed interactive dashboards using Shiny to present research findings effectively.",
        "color": "#F27D26",
    },
    {
        "id": "flex",
        "title": "Flex",
        "summary": "Dynamic branding system.<br/>Flexible design components.",
        "desc": "Dynamic branding system.",
        "color": "#EF4444",
    },
    {
        "id": "utility-2",
        "title": "Utility",
        "desc": "Technical instrumentation suite.",
        "color": "#EC4899",
    },
    {
        "id": "home",
        "title": "Smart Home",
        "summary": "Home Automation & Integration<br/>Reliable services on Kubernetes",
        "desc": "Bring Home Assistant, Frigate, HomeBridge, and more to the smart home. Enables seamless integration and control of various smart devices, creating a unified and efficient smart home ecosystem. Apple HomeKit, Google Home, Amazon Alexa, and more.",
        "color": "#8B5CF6",
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
