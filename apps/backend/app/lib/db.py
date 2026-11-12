from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.lib.config import get_settings

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Parent of every table. Just a schema marker, no logic."""
    # Predictable constraint names, e.g. "uq_users_email", so migrations stay clean
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })


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