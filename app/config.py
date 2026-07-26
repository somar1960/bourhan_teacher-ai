from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Telegram
    admin_bot_token: str
    student_bot_token: str
    owner_telegram_id: int

    # Database
    database_url: str

    # AI (اختياري)
    openai_api_key: Optional[str] = None

    # Redis (اختياري)
    redis_url: Optional[str] = None

    # Proxy (اختياري) - أضف هذا السطر
    telegram_proxy: Optional[str] = None

    # App
    environment: str = "development"
    timezone: str = "Asia/Damascus"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

settings = Settings()
