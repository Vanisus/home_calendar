import hashlib
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
import recurring_ical_events
from icalendar import Calendar

from app.calendars.models import CalendarEvent, SourceConfig

MAX_CALENDAR_BYTES = 5 * 1024 * 1024


async def download_calendar(
    client: httpx.AsyncClient,
    source: SourceConfig,
) -> bytes:
    async with client.stream("GET", source.url) as response:
        response.raise_for_status()

        data = bytearray()

        async for chunk in response.aiter_bytes():
            data.extend(chunk)

            if len(data) > MAX_CALENDAR_BYTES:
                raise ValueError("Calendar exceeds size limit")

    return bytes(data)


def as_local_datetime(
    value: date | datetime,
    timezone: ZoneInfo,
) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone)

        return value.astimezone(timezone)

    return datetime.combine(value, time.min, tzinfo=timezone)


def parse_calendar(
    raw: bytes,
    source: SourceConfig,
    timezone: ZoneInfo,
    window_start: datetime,
    window_end: datetime,
) -> list[CalendarEvent]:
    calendar = Calendar.from_ical(raw)

    if calendar.name != "VCALENDAR":
        raise ValueError("Calendar is not VCALENDAR")

    occurrences = recurring_ical_events.of(calendar).between(
        window_start,
        window_end,
    )

    events = []

    for component in occurrences:
        if component.name != "VEVENT":
            continue

        if str(component.get("STATUS", "")).upper() == "CANCELLED":
            continue

        raw_start = component.decoded("DTSTART")
        all_day = not isinstance(raw_start, datetime)

        start = as_local_datetime(raw_start, timezone)

        if "DTEND" in component:
            end = as_local_datetime(
                component.decoded("DTEND"),
                timezone,
            )
        elif "DURATION" in component:
            end = start + component.decoded("DURATION")
        else:
            end = start + (timedelta(days=1) if all_day else timedelta())

        if end < start:
            raise ValueError("Event end precedes its start")

        overlaps = start < window_end and (
            end > window_start
            or (start == end and start >= window_start)
        )

        if not overlaps:
            continue

        uid = str(component.get("UID", ""))

        if not uid:
            raise ValueError("Event has no UID")

        occurrence_key = f"{source.id}|{uid}|{start.isoformat()}"
        event_id = hashlib.sha256(
            occurrence_key.encode("utf-8")
        ).hexdigest()

        events.append(
            CalendarEvent(
                id=event_id,
                source_id=source.id,
                source_name=source.name,
                color=source.color,
                title=str(component.get("SUMMARY", "Без названия")),
                description=str(component.get("DESCRIPTION", "")),
                location=str(component.get("LOCATION", "")),
                all_day=all_day,
                start=start,
                end=end,
            )
        )

    return events
