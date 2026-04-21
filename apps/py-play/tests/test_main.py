from fastapi.testclient import TestClient
from web.main import app

client = TestClient(app)


def test_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
