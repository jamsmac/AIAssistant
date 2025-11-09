"""Database dependencies for FastAPI routes."""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import HTTPException, status

from agents.db_pool import db_pool


async def get_db_connection() -> AsyncIterator[object]:
    """Yield a database connection from the global pool."""
    if not db_pool.is_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool is not initialized",
        )

    async with db_pool.acquire() as connection:
        yield connection
