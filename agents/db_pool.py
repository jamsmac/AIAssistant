"""Database connection pooling for PostgreSQL using asyncpg."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Dict, Any

import asyncpg

logger = logging.getLogger(__name__)


class DatabasePool:
    """Async PostgreSQL connection pool manager."""

    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None
        self._dsn: Optional[str] = None

    async def initialize(
        self,
        dsn: Optional[str] = None,
        *,
        min_size: int = 10,
        max_size: int = 20,
        max_queries: int = 50_000,
        max_inactive_connection_lifetime: float = 300.0,
        command_timeout: float = 60.0,
        timeout: float = 30.0,
    ) -> asyncpg.Pool:
        """Initialize the connection pool if not already created."""
        if self.pool is not None:
            return self.pool

        self._dsn = dsn or os.getenv("DATABASE_URL")
        if not self._dsn:
            raise ValueError("DATABASE_URL environment variable is required to initialize the connection pool")

        logger.info(
            "Initializing PostgreSQL connection pool (min_size=%s, max_size=%s, max_queries=%s)",
            min_size,
            max_size,
            max_queries,
        )

        self.pool = await asyncpg.create_pool(
            dsn=self._dsn,
            min_size=min_size,
            max_size=max_size,
            max_queries=max_queries,
            max_inactive_connection_lifetime=max_inactive_connection_lifetime,
            command_timeout=command_timeout,
            timeout=timeout,
        )

        logger.info("PostgreSQL connection pool initialized successfully")
        return self.pool

    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection from the pool."""
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized. Call initialize() first.")

        async with self.pool.acquire() as connection:
            yield connection

    def is_initialized(self) -> bool:
        """Return True if the pool has been initialized."""
        return self.pool is not None

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the current pool state."""
        if self.pool is None:
            return {
                "initialized": False,
                "size": 0,
                "max_size": 0,
                "min_size": 0,
                "idle_connections": 0,
                "in_use_connections": 0,
                "dsn": self._dsn,
            }

        size = self.pool.get_size()
        idle_getter = getattr(self.pool, "get_idle_count", None)
        if idle_getter is None:
            idle_getter = getattr(self.pool, "get_idle_size", None)
        idle = idle_getter() if idle_getter else 0
        max_size = self.pool.get_max_size()
        min_size = self.pool.get_min_size()
        in_use = max(size - idle, 0)

        return {
            "initialized": True,
            "size": size,
            "max_size": max_size,
            "min_size": min_size,
            "idle_connections": idle,
            "free_connections": idle,
            "in_use_connections": in_use,
            "dsn": self._dsn,
        }


# Global pool instance
_db_pool = DatabasePool()


def get_db_pool() -> DatabasePool:
    """Expose the global database pool instance."""
    return _db_pool


# Backwards-compatible alias
db_pool = get_db_pool()
