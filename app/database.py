from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG, 
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
Base = declarative_base()


# Private session factory base function
async def _create_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Session Factory for FastAPI dependency injection
get_db = _create_db_session

# Session factory with asynccontextmanager for manual use
get_db_session = asynccontextmanager(_create_db_session)
