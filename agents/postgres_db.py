"""
PostgreSQL Database Manager
Manages async PostgreSQL connections using asyncpg
"""
import asyncpg
import os
import logging
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class PostgresDB:
    """
    Async PostgreSQL database manager
    Handles connection pooling and query execution
    """

    def __init__(self, database_url: Optional[str] = None):
        """Initialize with database URL"""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not provided")

        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        if self.pool is None:
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    timeout=30
                )
                logger.info("PostgreSQL connection pool created")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query that doesn't return rows (INSERT, UPDATE, DELETE)
        Returns: status string (e.g., "INSERT 0 1")
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, *args)
                return result
        except Exception as e:
            logger.error(f"Execute error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Args: {args}")
            raise

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute a query and return all rows
        Returns: List of dicts
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Args: {args}")
            raise

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """
        Execute a query and return single row
        Returns: Dict or None
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Fetchrow error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Args: {args}")
            raise

    async def fetchval(self, query: str, *args) -> Any:
        """
        Execute a query and return single value
        Returns: Any value or None
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                value = await conn.fetchval(query, *args)
                return value
        except Exception as e:
            logger.error(f"Fetchval error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Args: {args}")
            raise

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions

        Usage:
            async with db.transaction():
                await db.execute("INSERT ...")
                await db.execute("UPDATE ...")
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """
        Execute same query multiple times with different args
        Useful for batch inserts
        """
        if not self.pool:
            await self.connect()

        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(query, args_list)
        except Exception as e:
            logger.error(f"Execute many error: {e}")
            logger.error(f"Query: {query}")
            raise

    async def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        result = await self.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = $1
            )
        """, table_name)
        return result

    async def get_tables(self) -> List[str]:
        """Get list of all tables"""
        rows = await self.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        return [row['table_name'] for row in rows]

    async def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        rows = await self.fetch("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)
        return rows


# Global database instance
_db_instance: Optional[PostgresDB] = None


def get_db() -> PostgresDB:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDB()
    return _db_instance


async def init_db():
    """Initialize database connection"""
    db = get_db()
    await db.connect()
    return db


async def close_db():
    """Close database connection"""
    global _db_instance
    if _db_instance:
        await _db_instance.disconnect()
        _db_instance = None
