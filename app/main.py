from contextlib import asynccontextmanager
from time import monotonic
from zoneinfo import ZoneInfo

import uvicorn
from fastapi import FastAPI

from app.api import system_router
from app.config import get_settings, setup_logger, settings

logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.settings = settings
    app.state.timezone = ZoneInfo(settings.timezone)
    app.state.started_at = monotonic()

    logger.info(
        "Starting %s: timezone: %s",
        settings.app_name,
        settings.timezone,
    )

    try:
        yield
    finally:
        logger.info(
            "Stopping %s",
            settings.app_name,
        )

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(
        system_router,
        prefix="/api/v1",
    )

    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
