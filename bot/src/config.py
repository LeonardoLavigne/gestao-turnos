from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List
from functools import lru_cache
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Gestão de Turnos"
    timezone: str = Field(default="America/Sao_Paulo", validation_alias="APP_TIMEZONE")

    # API Connection
    base_url: str = "http://localhost:8000"
    internal_api_key: str

    # Execution Mode (polling / webhook)
    execution_mode: str = Field(default="polling", validation_alias="MODE")
    host: str = "0.0.0.0"
    port: int = 8000
    webhook_url: Optional[str] = None

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_users: List[int] = []

    @field_validator("telegram_allowed_users", mode="before")
    @classmethod
    def parse_allowed_users(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


