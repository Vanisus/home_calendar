from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=2,
        max_overflow=1,
        pool_pre_ping=True,
    )

def create_session_factory(
        engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)