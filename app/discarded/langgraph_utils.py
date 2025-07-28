"""Utilities for LangGraph integration."""

import asyncio
from typing import Optional
from urllib.parse import urlparse

import psycopg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


async def get_langgraph_checkpointer() -> AsyncPostgresSaver:
    """Create a LangGraph checkpointer that doesn't conflict with asyncpg."""

    # Create connection pool
    pool = AsyncConnectionPool(
        conninfo=settings.PSYCOPG3_DATABASE_URL,
        min_size=1,
        max_size=3,
        timeout=30,
        kwargs={
            "prepare_threshold": 0,  # Disable automatic prepared statement creation
            "autocommit": True,
            "row_factory": dict_row,
        },
    )

    # Create checkpointer with the pool
    checkpointer = AsyncPostgresSaver(pool)

    return checkpointer


async def get_next_thread_id_from_checkpointer(checkpointer: AsyncPostgresSaver) -> str:
    """Get next sequential thread ID from the checkpointer's connection."""
    async with checkpointer._get_async_connection() as conn:
        async with conn.cursor() as cur:
            # Query from the langgraph schema
            await cur.execute("""
                SELECT COALESCE(MAX(CAST(thread_id AS INTEGER)), 0) + 1 
                FROM langgraph.checkpoints 
                WHERE thread_id ~ '^[0-9]+$'
            """)
            result = await cur.fetchone()
            return str(result[0])


async def close_checkpointer(checkpointer: AsyncPostgresSaver) -> None:
    """Properly close the checkpointer and its connections."""
    if hasattr(checkpointer, "async_connection") and checkpointer.async_connection:
        if hasattr(checkpointer.async_connection, "close"):
            await checkpointer.async_connection.close()
