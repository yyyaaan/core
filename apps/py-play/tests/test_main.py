import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from pydantic import SecretStr

from play import auth, main
from play.config import Settings, get_settings
from play.digest.build import Digest

client = TestClient(main.app)

TEAM = "https://team.cloudflareaccess.com"
AUD = "aud-play-private"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def access_token(key=KEY, **overrides):
    now = int(time.time())
    claims = {
        "iss": TEAM,
        "aud": [AUD],
        "email": "Yan@Yan.fi",
        "iat": now,
        "exp": now + 60,
    } | overrides
    return jwt.encode(claims, key, algorithm="RS256")


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    settings = Settings(
        access_team_domain=TEAM,
        access_aud=AUD,
        internal_token="s3cret",
        allow_local_auth=False,
    )
    main.app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(auth, "_signing_key", lambda token, team: KEY.public_key())
    yield settings
    main.app.dependency_overrides.clear()


def view(**headers):
    return client.get("/view", headers=headers)


def test_root_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["message"] == "server is up"


def test_view_requires_auth():
    assert view().status_code == 401


def test_client_sent_email_headers_are_ignored():
    spoofed = {"X-Auth-Request-Email": "yan@yan.fi", "X-Forwarded-Email": "yan@yan.fi"}
    assert view(**spoofed).status_code == 401
    assert (
        view(**{"Cf-Access-Authenticated-User-Email": "yan@yan.fi"}).status_code == 401
    )


@pytest.mark.parametrize(
    "token",
    [
        lambda: access_token(aud=["another-app"]),
        lambda: access_token(iss="https://evil.cloudflareaccess.com"),
        lambda: access_token(exp=int(time.time()) - 10),
        lambda: access_token(key=OTHER_KEY),
        lambda: jwt.encode({"iss": TEAM, "aud": [AUD]}, "x" * 32, algorithm="HS256"),
        lambda: "not-a-jwt",
    ],
    ids=["aud", "iss", "expired", "signature", "alg", "garbage"],
)
def test_bad_access_token_is_rejected(token):
    assert view(**{"Cf-Access-Jwt-Assertion": token()}).status_code == 401


def test_bad_access_token_does_not_fall_back(_settings):
    _settings.allow_local_auth = True
    _settings.local_auth_email = "t@t.dev"
    headers = {"Cf-Access-Jwt-Assertion": "not-a-jwt", "Authorization": "Bearer s3cret"}
    assert view(**headers).status_code == 401


def test_unconfigured_access_fails_closed(_settings):
    _settings.access_aud = ""
    assert view(**{"Cf-Access-Jwt-Assertion": access_token()}).status_code == 401


def test_internal_token(_settings):
    assert view(Authorization="Bearer wrong").status_code == 401
    assert view(Authorization="Basic s3cret").status_code == 401
    _settings.internal_token = SecretStr("")
    assert view(Authorization="Bearer ").status_code == 401


def test_local_auth(_settings, monkeypatch):
    _settings.allow_local_auth = True
    _settings.local_auth_email = "t@t.dev"

    async def digest(refresh=False):
        return Digest(title="t", html="<p>d</p>")

    monkeypatch.setattr(main, "get_digest", digest)
    assert view().status_code == 200


def test_view_and_scheduled(monkeypatch):
    sent = []

    async def digest(refresh=False):
        return Digest(title="t", html="<p>d</p>")

    async def send(subject, html, recipients):
        sent.append(recipients)

    monkeypatch.setattr(main, "get_digest", digest)
    monkeypatch.setattr(main, "send_email", send)
    user = {"Cf-Access-Jwt-Assertion": access_token()}
    cron = {"Authorization": "Bearer s3cret"}
    assert client.get("/view", headers=user).text == "<p>d</p>"
    assert client.post("/scheduled?audience=0", headers=user).json() == {
        "title": "t",
        "sent_to": 0,
    }
    assert client.post("/scheduled?audience=2", headers=cron).json()["sent_to"] == 2
    assert sent == [["yan@yan.fi", "lixiaoyuan23@gmail.com"]]


def test_upstream_failure_is_502(monkeypatch):
    async def down(now):
        raise httpx.ConnectError("frigate down")

    monkeypatch.setattr(main.spot_chart, "html", down)
    response = client.get("/public/spot")
    assert response.status_code == 502
