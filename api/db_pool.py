"""
Database Connection Pool for PostgreSQL
Provides asyncpg pool for API routes
"""

import asyncpg
import os
from typing import Optional

_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Get or create database connection pool

    Returns:
        asyncpg.Pool: Database connection pool
    """
    global _pool

    if _pool is None:
        database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/autopilot')

        _pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )

    return _pool


async def close_db_pool():
    """Close the database connection pool"""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None
