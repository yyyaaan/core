from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # auth (oauth2-proxy headers)
    auth_url: str = "https://auth.yan.fi/oauth2/start"
    allowed_emails: list[str] = ["yan@yan.fi", "internal@kube.system"]
    allow_local_auth: bool = False
    local_auth_email: str | None = None

    tz: str = "Europe/Helsinki"  # TZ from the tz-config secret

    # digest email (SMTP2GO_API_KEY from the email-credentials secret)
    smtp2go_api_key: SecretStr = SecretStr("")
    email_sender: str = "bot@yanpan.fi"
    email_recipients: list[str] = ["yan@yan.fi", "lixiaoyuan23@gmail.com"]

    frigate_url: str = "http://frigate-service.home-internal.svc.cluster.local:5000"

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


@lru_cache
def get_settings() -> Settings:
    return Settings()
