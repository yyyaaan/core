"""
Private routes accept, in order:
- a Cloudflare Access token (`Cf-Access-Jwt-Assertion`), verified against the team's keys;
  the Access policy is the user list, so there is no allowlist here
- `Authorization: Bearer $INTERNAL_TOKEN`, for in-cluster callers (the mailing CronJob)
- locally: ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev uv run play-dev
Unset ACCESS_TEAM_DOMAIN / ACCESS_AUD / INTERNAL_TOKEN disable that path (fail closed).
"""

import asyncio
import logging
from functools import lru_cache
from hmac import compare_digest

import jwt
from fastapi import Depends, Header, HTTPException, Request

from play.config import Settings, get_settings

log = logging.getLogger(__name__)


@lru_cache
def _jwks(team_domain: str) -> jwt.PyJWKClient:
    # caches keys; refetches on an unknown kid (Access rotates keys)
    return jwt.PyJWKClient(f"{team_domain}/cdn-cgi/access/certs", timeout=10)


def _signing_key(token: str, team_domain: str):
    return _jwks(team_domain).get_signing_key_from_jwt(token).key


async def _access_email(token: str, settings: Settings) -> str:
    team_domain = settings.access_team_domain.rstrip("/")
    if not team_domain or not settings.access_aud:
        raise HTTPException(401, "Access token validation is not configured")
    try:
        key = await asyncio.to_thread(_signing_key, token, team_domain)
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.access_aud,
            issuer=team_domain,
            options={"require": ["exp", "iat", "aud", "iss"]},
        )
    except jwt.PyJWTError as exc:
        log.warning("rejected Access token: %s", exc)
        raise HTTPException(401, "Invalid Access token") from exc
    # service tokens carry common_name instead of email
    return (claims.get("email") or claims.get("common_name") or claims["sub"]).lower()


async def require_user(
    request: Request,
    cf_access_jwt_assertion: str | None = Header(None),
    authorization: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    if cf_access_jwt_assertion:
        return await _access_email(cf_access_jwt_assertion, settings)

    internal = settings.internal_token.get_secret_value()
    scheme, _, credential = (authorization or "").partition(" ")
    if internal and scheme.lower() == "bearer":
        if compare_digest(credential.strip().encode(), internal.encode()):
            return "internal"
        log.warning("bad internal token on %s", request.url.path)

    if settings.allow_local_auth and settings.local_auth_email:
        return settings.local_auth_email.lower().strip()
    raise HTTPException(401, "Authentication required")
