from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "loveable-api"
    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False
    database_url: PostgresDsn
    jwt_secret: str
    jwt_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()