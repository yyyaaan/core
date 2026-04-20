"""
Authentication based header (X-Forwarded-Email) verification from OAUTH proxy.
To test locally, using curl or environment variables:
(a) curl -H 'X-Forwarded-Email: yan@yan.fi' http://localhost:7999/view
(b) ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play
"""

from fastapi import Depends, Header, HTTPException

from play.config import Settings, get_settings


def _normalize_email(email: str) -> str:
    return email.lower().strip()


async def require_user(
    x_forwarded_email: str | None = Header(None),
    x_auth_request_email: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    FastAPI dependency: verifies X-Forwarded-Email (set by oauth2-proxy)
    is in the allowed list. Returns the verified email.
    """
    email = x_forwarded_email or x_auth_request_email
    if email:
        normalized_email = _normalize_email(email)
    elif settings.allow_local_auth and settings.local_auth_email:
        normalized_email = _normalize_email(settings.local_auth_email)
    else:
        raise HTTPException(status_code=401, detail="Missing authentication header")

    if normalized_email not in settings.allowed_emails:
        raise HTTPException(status_code=403, detail="User not authorized")

    return normalized_email
