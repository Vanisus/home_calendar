import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class CalendarSourceORM(Base):
    __tablename__ = 'calendar_sources'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100))
    provider_type: Mapped[str] = mapped_column(
        String(20),
        default="ics",
        server_default="ics",
    )
    url: Mapped[str] = mapped_column(
        Text
    )
    color: Mapped[str] = mapped_column(
        String(7),
        default="#4285F4",
        server_default="#4285F4"
    )
    enabled: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
