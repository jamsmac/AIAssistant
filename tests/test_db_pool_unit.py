import asyncio
from unittest.mock import AsyncMock

import pytest

from agents.db_pool import DatabasePool


class DummyPool:
    def __init__(self, connection):
        self.connection = connection
        self._size = 5
        self._idle = 3
        self._max = 10
        self._min = 2

    def get_size(self):
        return self._size

    def get_idle_count(self):
        return self._idle

    def get_max_size(self):
        return self._max

    def get_min_size(self):
        return self._min

    def acquire(self):
        class _CM:
            async def __aenter__(self_inner):
                return self.connection

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return _CM()

    async def close(self):
        self._size = 0
        self._idle = 0


@pytest.mark.asyncio
async def test_database_pool_initialize(monkeypatch):
    connection = object()
    dummy_pool = DummyPool(connection)

    async_create_pool = AsyncMock(return_value=dummy_pool)
    monkeypatch.setattr("agents.db_pool.asyncpg.create_pool", async_create_pool)

    pool = DatabasePool()
    result = await pool.initialize(
        dsn="postgresql://user:pass@localhost:5432/db",
        min_size=2,
        max_size=4,
        max_queries=100,
        max_inactive_connection_lifetime=120,
        command_timeout=30,
        timeout=15,
    )

    assert result is dummy_pool
    async_create_pool.assert_awaited_once()
    assert pool.is_initialized()

    stats = pool.get_stats()
    assert stats["initialized"] is True
    assert stats["size"] == 5
    assert stats["idle_connections"] == 3

    async with pool.acquire() as conn:
        assert conn is connection

    await pool.close()
    assert pool.get_stats()["initialized"] is False
