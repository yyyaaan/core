"""HTML email via SMTP2GO's MIME endpoint."""

import logging
from base64 import b64encode
from email.message import EmailMessage

from play.config import get_settings
from play.httpclient import client

log = logging.getLogger(__name__)

API_URL = "https://api.smtp2go.com/v3/email/mime"


def build_mime(sender: str, recipients: list[str], subject: str, html: str) -> bytes:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")
    return msg.as_bytes()


async def send_email(subject: str, html: str, recipients: list[str]) -> None:
    s = get_settings()
    mime = build_mime(s.email_sender, recipients, subject, html)
    async with client() as c:
        r = await c.post(
            API_URL,
            headers={"X-Smtp2go-Api-Key": s.smtp2go_api_key.get_secret_value()},
            json={"mime_email": b64encode(mime).decode()},
        )
    log.info("smtp2go %s %s", r.status_code, r.text)
    r.raise_for_status()
    if r.json().get("data", {}).get("failed"):
        raise RuntimeError(f"smtp2go rejected the email: {r.text}")
