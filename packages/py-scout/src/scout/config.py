from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SCOUT_")

    cdp_url: str | None = None  # default: resolved in cdp.endpoint()
    cdp_port: int = 9222
    db_path: Path = Path(__file__).resolve().parents[2] / "data" / "scout.sqlite"

    # pause between requests, seconds (randomised in this range)
    delay_min: float = 2.0
    delay_max: float = 4.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
