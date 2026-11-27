from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response
from app.calendars.models import AgendaResponse, SourceStatus

router = APIRouter(tags=["calendars"])

@router.get("/calendars", response_model=list[SourceStatus])
async def list_calendars(
        request: Request,
        response: Response,
) -> list[SourceStatus]:
    response.headers["Cache-Control"] = "no-store"

    today = datetime.now(request.app.state.timezone).date()
    agenda = request.app.state.calendar_service.get_agenda(
        today,
        today
    )

    return agenda.sources

@router.get("/agenda", response_model=AgendaResponse)
async def get_agenda(
    request: Request,
    response: Response,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AgendaResponse:
    response.headers["Cache-Control"] = "no-store"

    start = start_date or datetime.now(
        request.app.state.timezone
    ).date()

    end = end_date or start + timedelta(days=6)

    try:
        return request.app.state.calendar_service.get_agenda(
            start,
            end,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc