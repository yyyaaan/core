"""
Authentication based header (X-Forwarded-Email) verification from OAUTH proxy.
To test locally, using curl or environment variables:
(a) curl -H 'X-Forwarded-Email: yan@yan.fi' http://localhost:7999/view
(b) ALLOW_LOCAL_AUTH=true LOCAL_AUTH_EMAIL=t@t.dev ALLOWED_EMAILS='["t@t.dev"]' uv run play
"""

from urllib.parse import urlencode

from fastapi import Depends, Header, HTTPException, Request

from play.config import Settings, get_settings


async def require_user(
    request: Request,
    x_forwarded_email: str | None = Header(None),
    x_auth_request_email: str | None = Header(None),
    settings: Settings = Depends(get_settings),
) -> str:
    """
    FastAPI dependency: verifies X-Forwarded-Email (set by oauth2-proxy)
    is in the allowed list. Returns the verified email.
    """
    auth_url = f"{get_settings().auth_url}?{urlencode({'rd': str(request.url)})}"

    email = x_forwarded_email or x_auth_request_email
    if email:
        normalized_email = email.lower().strip()
    elif settings.allow_local_auth and settings.local_auth_email:
        normalized_email = settings.local_auth_email.lower().strip()
    else:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"Location": auth_url})
        # raise HTTPException(
        #     status_code=307,
        #     detail="Redirecting to authentication",
        #     headers={"Location": auth_url},
        # )

    if normalized_email not in settings.allowed_emails:
        raise HTTPException(status_code=403, detail="User not authorized")

    return normalized_email
