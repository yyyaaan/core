from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # auth (Cloudflare Access; all three from the play-credentials secret)
    access_team_domain: str = ""  # https://<team>.cloudflareaccess.com
    access_aud: str = ""  # application ID of the play-private Access app
    internal_token: SecretStr = SecretStr("")  # in-cluster callers
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
