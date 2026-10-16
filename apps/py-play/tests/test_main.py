import httpx
from fastapi.testclient import TestClient

from play import main
from play.digest.build import Digest

client = TestClient(main.app)
AUTH = {"X-Forwarded-Email": "yan@yan.fi"}


def test_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["message"] == "server is up"


def test_view_requires_auth():
    assert client.get("/view").status_code == 401
    assert (
        client.get("/view", headers={"X-Forwarded-Email": "who@x.dev"}).status_code
        == 403
    )


def test_view_and_scheduled(monkeypatch):
    sent = []

    async def digest(refresh=False):
        return Digest(title="t", html="<p>d</p>")

    async def send(subject, html, recipients):
        sent.append(recipients)

    monkeypatch.setattr(main, "get_digest", digest)
    monkeypatch.setattr(main, "send_email", send)
    assert client.get("/view", headers=AUTH).text == "<p>d</p>"
    assert client.post("/scheduled?audience=0", headers=AUTH).json() == {
        "title": "t",
        "sent_to": 0,
    }
    assert client.post("/scheduled?audience=2", headers=AUTH).json()["sent_to"] == 2
    assert sent == [["yan@yan.fi", "lixiaoyuan23@gmail.com"]]


def test_upstream_failure_is_502(monkeypatch):
    async def down(now):
        raise httpx.ConnectError("frigate down")

    monkeypatch.setattr(main.spot_chart, "html", down)
    response = client.get("/public/spot")
    assert response.status_code == 502
