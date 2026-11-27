import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx

from app.calendars.ics import download_calendar, parse_calendar
from app.calendars.models import (
    AgendaResponse,
    CalendarEvent,
    SourceConfig,
    SourceStatus,
)
from app.calendars.repository import CalendarSourceRepository
from app.config import Settings


logger = logging.getLogger("homeboard.calendars")


class CalendarService:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
        sources: CalendarSourceRepository,
    ):
        self.settings = settings
        self.client = client
        self.sources = sources
        self.timezone = ZoneInfo(settings.timezone)

        self._wakeup = asyncio.Event()
        self._events: dict[str, list[CalendarEvent]] = {}
        self._statuses: dict[str, SourceStatus] = {}

    def request_refresh(self) -> None:
        self._wakeup.set()

    async def run(self) -> None:
        while True:
            self._wakeup.clear()

            try:
                await self.refresh()
            except Exception:
                logger.exception("Calendar refresh failed")

            try:
                await asyncio.wait_for(
                    self._wakeup.wait(),
                    timeout=self.settings.calendar_refresh_seconds,
                )
            except asyncio.TimeoutError:
                pass

    async def refresh(self) -> None:
        rows = await self.sources.list_enabled()
        configs = [
            SourceConfig(
                id=str(row.id),
                name=row.name,
                url=row.url,
                color=row.color,
            )
            for row in rows
        ]
        active = {config.id for config in configs}

        for source_id in list(self._events):
            if source_id not in active:
                del self._events[source_id]

        for source_id in list(self._statuses):
            if source_id not in active:
                del self._statuses[source_id]

        today = datetime.now(self.timezone).date()
        window_start = datetime.combine(
            today, time.min, tzinfo=self.timezone
        )
        window_end = window_start + timedelta(
            days=self.settings.calendar_days_ahead
        )

        for config in configs:
            status = self._statuses.get(config.id) or SourceStatus(
                id=config.id, name=config.name, color=config.color
            )
            status.name = config.name
            status.color = config.color
            status.last_attempt_at = datetime.now(timezone.utc)
            self._statuses[config.id] = status

            try:
                raw = await download_calendar(self.client, config)
                events = await asyncio.to_thread(
                    parse_calendar,
                    raw,
                    config,
                    self.timezone,
                    window_start,
                    window_end,
                )
            except Exception as exc:
                status.state = "error"
                status.error = type(exc).__name__
            else:
                self._events[config.id] = events
                status.state = "ok"
                status.error = None
                status.last_success_at = datetime.now(timezone.utc)

    def get_agenda(
        self, start_date: date, end_date: date
    ) -> AgendaResponse:
        today = datetime.now(self.timezone).date()
        last_date = today + timedelta(
            days=self.settings.calendar_days_ahead - 1
        )

        if end_date < start_date:
            raise ValueError("end_date must not precede start_date")

        if start_date < today or end_date > last_date:
            raise ValueError(
                f"Supported dates: {today.isoformat()} "
                f"through {last_date.isoformat()}"
            )

        start = datetime.combine(
            start_date, time.min, tzinfo=self.timezone
        )
        end = datetime.combine(
            end_date + timedelta(days=1), time.min, tzinfo=self.timezone
        )

        events = [
            event
            for source_events in self._events.values()
            for event in source_events
            if event.start < end
            and (
                event.end > start
                or (event.start == event.end and event.start >= start)
            )
        ]

        events.sort(
            key=lambda e: (
                max(e.start.date(), start_date),
                not e.all_day,
                e.start,
                e.source_id,
                e.id,
            )
        )

        return AgendaResponse(
            timezone=self.settings.timezone,
            start_date=start_date,
            end_date=end_date,
            events=events,
            sources=[
                status.model_copy(deep=True)
                for status in self._statuses.values()
            ],
        )
