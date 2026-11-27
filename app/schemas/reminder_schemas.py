from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ReminderCreate(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )
    title: str = Field(
        min_length=1,
        max_length=200
    )
    notes: str = Field(
        default="",
        max_length=2000,
    )
    due_at: datetime | None = None
    list_name: str = Field(
        default="Общие",
        min_length=1,
        max_length=50
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=2
    )

class ReminderUpdate(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        str_strip_whitespace=True,
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )
    due_at: datetime | None = None
    list_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )
    priority: int | None = Field(
        default=0,
        ge=0,
        le=2
    )

class DoneUpdate(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    done: bool

class ReminderRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )
    id: UUID
    title: str
    notes: str
    due_at: datetime | None
    list_name: str | None
    priority: int
    done_at: datetime | None
    created_at: datetime | None
