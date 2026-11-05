from functools import lru_cache
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

class CalendarSource(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1)
    url: SecretStr
    color: str = Field(default="#4285F4", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: SecretStr) -> SecretStr:
        HttpUrl(value.get_secret_value())
        return value

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HOMEBOARD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_name: str = Field(default="HomeBoard", min_length=1)
    timezone: str = "Europe/Saratov"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"Unknown timezone: {value}"
            ) from exc

        return value

    @field_validator("calendars")
    @classmethod
    def validate_sources(
            cls,
            sources: list[CalendarSource],
    ) -> list[CalendarSource]:
        ids = [source.id for source in sources]

        if len(ids) != len(set(ids)):
            raise ValueError("Calendar source IDs must be unique")

        return sources

@lru_cache
def get_settings() -> Settings:
    return Settings()