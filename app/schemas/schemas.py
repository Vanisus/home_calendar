from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"

class SystemResponse(BaseModel):
    app_name: str
    version: str
    timezone: str
    server_time: datetime
    today: date
    tomorrow: date
    uptime_seconds: float