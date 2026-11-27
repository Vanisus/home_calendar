import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class ReminderORM(Base):
    __tablename__ = 'reminders'

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(200),
    )
    notes: Mapped[str] = mapped_column(
        Text,
        default="",
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    list_name: Mapped[str] = mapped_column(
        String(50),
        default="Общие",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    done: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True
    )
    done_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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
