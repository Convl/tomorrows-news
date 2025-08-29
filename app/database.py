import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    connect_args=settings.CONNECT_ARGS,
    # Recycle the connection to avoid connection issues.
    # See:
    # - https://github.com/orgs/supabase/discussions/27071
    pool_recycle=240,
    # Pre-ping the connection to avoid connecting to a closed connection.
    # See:
    # - https://github.com/orgs/supabase/discussions/27071
    pool_pre_ping=True,
    # Do not expire sessions on commit.
    # See:
    # - https://github.com/sqlalchemy/sqlalchemy/discussions/11495
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Base class for models
class Base(DeclarativeBase):
    pass


async def _create_db_session_with_retry() -> AsyncSession:
    """Create a database session with retry logic for connection timeouts."""
    max_retries = settings.DB_CONNECTION_RETRIES
    base_delay = settings.DB_RETRY_DELAY_BASE
    last_exception = None

    for attempt in range(max_retries):
        try:
            session = AsyncSessionLocal()
            # Test the connection immediately to catch timeout early
            await session.execute(text("SELECT 1"))
            return session
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = base_delay**attempt
                logger.warning(
                    f"Database connection attempt {attempt + 1}/{max_retries} failed, retrying in {wait_time}s: {type(e).__name__}"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "All {max_retries} database connection attempts failed. Last error: <red>{e}</red>",
                    max_retries=max_retries,
                    e=e,
                )

    raise last_exception


# Private session factory base function
async def _create_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    # session = await _create_db_session_with_retry()
    # try:
    #     yield session
    # finally:
    #     await session.close()


# Session Factory for FastAPI dependency injection
get_db = _create_db_session

# Session factory with asynccontextmanager for manual use
get_db_session = asynccontextmanager(_create_db_session)
