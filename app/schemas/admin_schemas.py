from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)

COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"


def _normalize_webcal(value):
    if isinstance(value, str) and value.lower().startswith("webcal://"):
        return "https://" + value[len("webcal://"):]
    return value


def _require_https(value: HttpUrl | None) -> HttpUrl | None:
    if value is not None and value.scheme != "https":
        raise ValueError("Only https URLs are supported")
    return value


class SourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    color: str = Field(default="#4285F4", pattern=COLOR_PATTERN)

    _normalize_url = field_validator("url", mode="before")(_normalize_webcal)
    _check_url = field_validator("url")(_require_https)


class SourceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    color: str | None = Field(default=None, pattern=COLOR_PATTERN)
    enabled: bool | None = None

    _normalize_url = field_validator("url", mode="before")(_normalize_webcal)
    _check_url = field_validator("url")(_require_https)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    provider_type: str
    color: str
    enabled: bool
    created_at: datetime
    updated_at: datetime