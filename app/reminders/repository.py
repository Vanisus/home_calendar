from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, delete, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import ReminderORM

EDITABLE = {
    "title",
    "notes",
    "due_at",
    "list_name",
    "priority",
}

class RemindersRepository:
    def __init__(
            self,
            session_factory: async_sessionmaker[AsyncSession],
    ):
        self._sf = session_factory

    async def list_active(
            self,
            done_within_minutes: int = 5
    ) -> list[ReminderORM]:
        cutoff = func.now() - timedelta(minutes=done_within_minutes)
        async with self._sf() as session:
            result = await session.scalars(
                select(ReminderORM)
                .where(
                    or_(
                        ReminderORM.done.is_(False),
                        and_(
                            ReminderORM.done.is_(True),
                            ReminderORM.done_at >= cutoff,
                        ),
                    )
                )
                .order_by(
                    ReminderORM.done,
                    ReminderORM.due_at.is_(None),
                    ReminderORM.due_at,
                    ReminderORM.priority.desc(),
                    ReminderORM.created_at,
                )
            )
            return list(result)

    async def create(
            self,
            **fields
    ) -> ReminderORM:
        async with self._sf() as session, session.begin():
            row = ReminderORM(**fields)
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return row

    async def update(
            self,
            reminder_id: UUID,
            **fields
    ) -> ReminderORM | None:
        async with self._sf() as session, session.begin():
            row = await session.get(ReminderORM, reminder_id)

            if row is None:
                return None

            for key, value in fields.items():
                setattr(row, key, value)

            await session.flush()
            await session.refresh(row)
            return row

    async def delete(
            self,
            reminder_id: UUID
    ) -> bool:
        async with self._sf() as session, session.begin():
            row = await session.get(ReminderORM, reminder_id)

            if row is None:
                return False

            await session.delete(row)
            return True

    async def set_done(
            self,
            reminder_id: UUID,
            done: bool
    ) -> ReminderORM | None:
        async with self._sf() as session, session.begin():
            row = await session.get(ReminderORM, reminder_id)

            if row is None:
                return None

            if row.done != done:
                row.done = done
                row.done_at = func.now() if done else None
                await session.flush()
                await session.refresh(row)

            return row

    async def purge_done(
            self,
            older_than_days: int = 7
    ) -> int:
        cutoff = func.now() - timedelta(days=older_than_days)

        async with self._sf() as session, session.begin():
            result = await session.execute(
                delete(ReminderORM).where(
                    ReminderORM.done.is_(True),
                    ReminderORM.done_at < cutoff,
                )
            )
            return result.rowcount or 0