from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfoNotFoundError, ZoneInfo

from pydantic import (
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HOMEBOARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Homeboard"
    timezone: str = "Europe/Saratov"
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"

    database_url: str
    admin_token: SecretStr = Field(min_length=16)

    calendar_refresh_seconds: int = Field(default=300, ge=30)
    calendar_days_ahead: int = Field(default=60, ge=7, le=366)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc
        return value


@lru_cache
def get_settings() -> Settings:
    # noinspection PyArgumentList
    return Settings()
