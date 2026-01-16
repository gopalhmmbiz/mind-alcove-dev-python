from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


# -------------------------------------------------------------------
# Engine
# -------------------------------------------------------------------

def _build_async_db_url() -> str:
    return (
        f"mysql+aiomysql://{settings.db_user}:"
        f"{settings.db_password}@"
        f"{settings.db_host}:"
        f"{settings.db_port}/"
        f"{settings.db_name}"
    )


async_engine: AsyncEngine = create_async_engine(
    _build_async_db_url(),
    echo=settings.debug,
    pool_pre_ping=True,
)


# -------------------------------------------------------------------
# Session factory
# -------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -------------------------------------------------------------------
# Dependency (for FastAPI injection)
# -------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# -------------------------------------------------------------------
# Lifecycle hooks (for FastAPI lifespan)
# -------------------------------------------------------------------

async def init_db() -> None:
    """
    Validate database connectivity at application startup.
    Does not create long-lived connections.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda _: None)


async def close_db() -> None:
    """
    Dispose the database connection pool at application shutdown.
    """
    await async_engine.dispose()
