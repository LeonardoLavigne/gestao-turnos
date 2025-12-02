from pydantic import BaseModel
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseModel):
    app_name: str = "Gestão de Turnos"
    timezone: str = os.getenv("APP_TIMEZONE", "America/Sao_Paulo")

    # DB
    # PostgreSQL (prioritário) ou SQLite (fallback)
    database_url: Optional[str] = os.getenv("DATABASE_URL", None)
    
    # Stripe Configuration
    stripe_api_key: str = os.getenv("STRIPE_API_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_price_id_pro: str = os.getenv("STRIPE_PRICE_ID_PRO", "")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")  # Para URLs de sucesso/cancelamento
    sqlite_path: str = os.getenv("SQLITE_PATH", "data/gestao_turnos.db")

    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_users: list[int] = []

    # CalDAV / Disroot
    caldav_url: str = os.getenv("CALDAV_URL", "")
    caldav_username: str = os.getenv("CALDAV_USERNAME", "")
    caldav_password: str = os.getenv("CALDAV_PASSWORD", "")
    caldav_calendar_path: str = os.getenv("CALDAV_CALENDAR_PATH", "")

    @classmethod
    def from_env(cls) -> "Settings":
        allowed_users_raw = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        allowed_users: list[int] = []
        for part in allowed_users_raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                allowed_users.append(int(part))
            except ValueError:
                continue

        base = cls()
        base.telegram_allowed_users = allowed_users
        return base


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


