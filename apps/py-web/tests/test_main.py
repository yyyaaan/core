from fastapi.testclient import TestClient
from web.main import app, projects

client = TestClient(app)


def test_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_root_contains_projects():
    response = client.get("/")
    assert response.status_code == 200
    # All project titles should appear in the rendered HTML
    for title in [p["title"] for p in projects]:
        assert title in response.text
