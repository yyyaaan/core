from fastapi.testclient import TestClient
from play.main import app

client = TestClient(app)


def test_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["message"] == "server is up"
