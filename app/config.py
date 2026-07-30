from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    admin_bot_token: str
    student_bot_token: str
    owner_telegram_id: int

    # Database
    database_url: str

    # AI
    openai_api_key: Optional[str] = None

    # Redis
    redis_url: Optional[str] = None

    # Telegram Proxy (اختياري)
    telegram_proxy: Optional[str] = None

    # App
    environment: str = "development"
    timezone: str = "Asia/Damascus"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()