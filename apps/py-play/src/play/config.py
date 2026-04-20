from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    auth_url: str = "https://auth.yan.fi/oauth2/start"
    allowed_emails: list[str] = ["yan@yan.fi", "internal@kube.system"]
    allow_local_auth: bool = False
    local_auth_email: str | None = None
    hour_bbc: int = 9


@lru_cache
def get_settings() -> Settings:
    return Settings()
