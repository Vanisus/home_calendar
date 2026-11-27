from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import CalendarSourceORM

class CalendarSourceRepository:
    def __init__(
            self,
            session_factory: async_sessionmaker[AsyncSession],
    ):
        self._sf = session_factory

    async def list_all(
            self
    ) -> list[CalendarSourceORM]:
        async with self._sf() as session:
            result = await session.scalars(
                select(
                    CalendarSourceORM
                )
                .order_by(
                    CalendarSourceORM.created_at,
                    CalendarSourceORM.id
                )
            )
            return list(result)

    async def list_enabled(
            self
    ) -> list[CalendarSourceORM]:
        async with self._sf() as session:
            result = await session.scalars(
                select(CalendarSourceORM)
                .where(
                    CalendarSourceORM.enabled.is_(True)
                )
                .order_by(
                    CalendarSourceORM.created_at,
                    CalendarSourceORM.id
                )
            )
            return list(result)

    async def create(
            self,
            *,
            name: str,
            url: str,
            color: str,
    ) -> CalendarSourceORM:
        async with self._sf() as session, session.begin():
            row = CalendarSourceORM(name=name, url=url, color=color)
            session.add(row)
            await session.flush()
            await session.refresh(row)
            return row

    async def update(
            self,
            source_id: UUID,
            **fields
    ) -> CalendarSourceORM | None:
        async with self._sf() as session, session.begin():
            row = await session.get(CalendarSourceORM, source_id)

            if row is None:
                return None

            for key, value in fields.items():
                setattr(row, key, value)

            await session.flush()
            await session.refresh(row)
            return row

    async def delete(
            self,
            source_id: UUID
    ) -> bool:
        async with self._sf() as session, session.begin():
            row = await session.get(CalendarSourceORM, source_id)

            if row is None:
                return False

            await session.delete(row)
            return True
