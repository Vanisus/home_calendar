from datetime import date, datetime

from pydantic import BaseModel

class CalendarEvent(BaseModel):
    id: str
    source_id: str
    source_name: str
    color: str

    title: str
    description: str
    location: str

    all_day: bool
    start: datetime
    end: datetime


class SourceStatus(BaseModel):
    id: str
    name: str
    color: str

    state: str = "pending"
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    error: str | None = None


class AgendaResponse(BaseModel):
    timezone: str
    start_date: date
    end_date: date
    events: list[CalendarEvent]
    sources: list[SourceStatus]
