from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    telegram_bot_token: str
    telegram_bot_username: str

    pass_token_secret: str

    organizer_telegram_ids: List[int]
    checkin_points: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()