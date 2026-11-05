from datetime import datetime, timedelta
from time import monotonic

from fastapi import APIRouter, Request, Response

from app.schemas import HealthResponse, SystemResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse()


@router.get("/system", response_model=SystemResponse)
async def system_info(
        request: Request,
        response: Response,
) -> SystemResponse:
    response.headers["Cache-Control"] = "no-store"

    settings = request.app.state.settings
    now = datetime.now(request.app.state.timezone)

    return SystemResponse(
        app_name=settings.app_name,
        version=request.app.version,
        timezone=settings.timezone,
        server_time=now,
        today=now.date(),
        tomorrow=now.date() + timedelta(days=1),
        uptime_seconds=round(
            monotonic() - request.app.state.started_at,
            3,
        ),
    )
