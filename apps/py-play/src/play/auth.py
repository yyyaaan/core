"""
Allowlist on X-Auth-Request-Email only: Traefik's oauth middleware overwrites it, whereas
client-sent X-Forwarded-Email passes through and oauth2-proxy admits any Google account.
Locally: curl -H 'X-Auth-Request-Email: yan@yan.fi' ..., or
ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play-dev
"""

import logging
from urllib.parse import urlencode

from fastapi import Depends, Header, HTTPException, Request

from play.config import Settings, get_settings

log = logging.getLogger(__name__)


async def require_user(
    request: Request,
    x_auth_request_email: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    email = x_auth_request_email
    if not email and settings.allow_local_auth:
        email = settings.local_auth_email
    if not email:
        auth_url = f"{settings.auth_url}?{urlencode({'rd': str(request.url)})}"
        raise HTTPException(
            401, f"Authentication required. Please authenticate at {auth_url}."
        )

    email = email.lower().strip()
    if email not in settings.allowed_emails:
        log.warning("unauthorized email %s on %s", email, request.url.path)
        raise HTTPException(403, "User not authorized")
    return email
