from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.lib.config import get_settings

# One connection pool for the whole app (like a Prisma client singleton)
engine = create_async_engine(
    str(get_settings().database_url),
    pool_pre_ping=True,  # check a connection is alive before using it
)

# Factory that creates a new session per request
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Give each request its own DB session and close it afterwards."""
    async with SessionLocal() as session:
        yield session