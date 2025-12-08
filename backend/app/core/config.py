from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, List, Union
from functools import lru_cache
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Gestão de Turnos"
    timezone: str = Field(validation_alias="APP_TIMEZONE")

    # DB
    database_url: Optional[str] = None
    sqlite_path: str = "data/gestao_turnos.db"
    
    # Logic
    free_tier_max_shifts: int = 30
    
    # Stripe Configuration
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_pro: str = ""
    base_url: str = "http://localhost:8000"

    # Telegram
    telegram_bot_token: str = ""
    telegram_allowed_users: List[int] = []
    
    # Security
    internal_api_key: str
    secret_key: str = Field(default="CHANGE_ME_IN_PROD", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24 * 7 # 7 days
    
    # CORS
    backend_cors_origins: Union[List[str], str] = []

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        if isinstance(v, (set, tuple)):
            return list(v)
        return []

    # CalDAV / Disroot
    caldav_url: str = ""
    caldav_username: str = ""
    caldav_password: str = ""
    caldav_calendar_path: str = ""

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


