import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from time import monotonic
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.calendars import router as calendars_router
from app.api.system import router as system_router
from app.calendars.repository import CalendarSourceRepository
from app.calendars.service import CalendarService
from app.config import get_settings
from app.db.session import create_engine, create_session_factory


logger = logging.getLogger("homeboard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.setLevel(settings.log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    engine = create_engine(settings.database_url)
    sources = CalendarSourceRepository(create_session_factory(engine))

    app.state.settings = settings
    app.state.timezone = ZoneInfo(settings.timezone)
    app.state.started_at = monotonic()
    app.state.sources = sources

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0),
            follow_redirects=True,
            limits=httpx.Limits(
                max_connections=2, max_keepalive_connections=2
            ),
        ) as client:
            service = CalendarService(settings, client, sources)
            app.state.calendar_service = service

            task = asyncio.create_task(
                service.run(), name="calendar-refresh"
            )
            logger.info("Starting %s", settings.app_name)

            try:
                yield
            finally:
                task.cancel()

                with suppress(asyncio.CancelledError):
                    await task

                logger.info("Stopping %s", settings.app_name)
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.3.0",
        lifespan=lifespan,
    )

    app.include_router(system_router, prefix="/api/v1")
    app.include_router(calendars_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    return app


app = create_app()
