"""
Database Connection Pool Module
Provides efficient database connection pooling for high-performance operations
"""

import asyncio
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, Any, List, Dict, AsyncGenerator
from pathlib import Path
import logging
import time
from queue import Queue, Empty
from threading import Lock, Thread
import atexit

logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"
DB_PATH.parent.mkdir(exist_ok=True)


class ConnectionPool:
    """
    Thread-safe SQLite connection pool
    SQLite doesn't support true async, so we use thread pool
    """

    def __init__(
        self,
        db_path: str = str(DB_PATH),
        min_size: int = 5,
        max_size: int = 20,
        timeout: float = 30.0
    ):
        """
        Initialize connection pool

        Args:
            db_path: Path to SQLite database
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed
            timeout: Timeout for acquiring connection
        """
        self.db_path = db_path
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout

        self._pool: Queue = Queue(maxsize=max_size)
        self._all_connections: List[sqlite3.Connection] = []
        self._lock = Lock()
        self._created_connections = 0
        self._active_connections = 0

        # Statistics
        self.stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'connections_reused': 0,
            'pool_exhausted_count': 0,
            'wait_time_total': 0.0,
            'queries_executed': 0
        }

        # Initialize minimum connections
        self._initialize_pool()

        # Register cleanup on exit
        atexit.register(self.close_all)

    def _initialize_pool(self):
        """Create initial minimum connections"""
        for _ in range(self.min_size):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )

        # Enable optimizations
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 134217728")  # 128MB mmap

        # Track connection
        with self._lock:
            self._all_connections.append(conn)
            self._created_connections += 1
            self.stats['connections_created'] += 1

        logger.debug(f"Created new connection (total: {self._created_connections})")
        return conn

    @contextmanager
    def acquire(self):
        """
        Acquire a connection from the pool

        Yields:
            sqlite3.Connection: Database connection
        """
        start_time = time.time()
        conn = None
        created_new = False

        try:
            # Try to get from pool
            try:
                conn = self._pool.get(timeout=0.1)
                self.stats['connections_reused'] += 1
            except Empty:
                # Pool is empty, try to create new if under limit
                with self._lock:
                    if self._created_connections < self.max_size:
                        conn = self._create_connection()
                        created_new = True
                    else:
                        # Pool exhausted, wait for connection
                        self.stats['pool_exhausted_count'] += 1
                        logger.warning(f"Connection pool exhausted (size: {self.max_size})")

                if not conn:
                    # Wait for a connection to be returned
                    conn = self._pool.get(timeout=self.timeout)
                    self.stats['connections_reused'] += 1

            # Update statistics
            wait_time = time.time() - start_time
            self.stats['wait_time_total'] += wait_time

            with self._lock:
                self._active_connections += 1

            # Test connection is alive
            conn.execute("SELECT 1")

            yield conn

        except Exception as e:
            logger.error(f"Error acquiring connection: {e}")
            raise

        finally:
            if conn:
                try:
                    # Return connection to pool
                    with self._lock:
                        self._active_connections -= 1

                    if not created_new or self._created_connections <= self.max_size:
                        self._pool.put(conn)
                    else:
                        # Close excess connection
                        conn.close()
                        with self._lock:
                            self._all_connections.remove(conn)
                            self._created_connections -= 1
                            self.stats['connections_closed'] += 1

                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    def execute(self, query: str, params: tuple = None) -> Any:
        """
        Execute a query using a pooled connection

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Query result
        """
        with self.acquire() as conn:
            cursor = conn.cursor()
            if params:
                result = cursor.execute(query, params)
            else:
                result = cursor.execute(query)
            conn.commit()
            self.stats['queries_executed'] += 1
            return result.fetchall()

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Execute multiple queries using a pooled connection

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        with self.acquire() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            self.stats['queries_executed'] += len(params_list)

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            return {
                **self.stats,
                'pool_size': self._pool.qsize(),
                'total_connections': self._created_connections,
                'active_connections': self._active_connections,
                'available_connections': self._pool.qsize(),
                'avg_wait_time': (
                    self.stats['wait_time_total'] / max(1, self.stats['connections_reused'])
                )
            }

    def close_all(self):
        """Close all connections in the pool"""
        logger.info("Closing connection pool...")

        # Close pooled connections
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
                self.stats['connections_closed'] += 1
            except Empty:
                break

        # Close any remaining connections
        with self._lock:
            for conn in self._all_connections:
                try:
                    conn.close()
                except:
                    pass
            self._all_connections.clear()
            self._created_connections = 0

        logger.info(f"Connection pool closed. Stats: {self.stats}")


class AsyncDatabasePool:
    """
    Async wrapper for database operations using connection pool
    Uses thread pool executor for async operations
    """

    def __init__(self, pool: ConnectionPool = None):
        """Initialize async database pool"""
        self.pool = pool or ConnectionPool()
        self._executor = None

    async def initialize(self):
        """Initialize async components"""
        import concurrent.futures
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.pool.max_size
        )

    async def close(self):
        """Close async components"""
        if self._executor:
            self._executor.shutdown(wait=True)
        self.pool.close_all()

    async def execute(self, query: str, params: tuple = None) -> List[Any]:
        """
        Execute query asynchronously

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.pool.execute,
            query,
            params
        )

    async def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Execute multiple queries asynchronously

        Args:
            query: SQL query
            params_list: List of parameter tuples
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.pool.execute_many,
            query,
            params_list
        )

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[sqlite3.Connection, None]:
        """
        Acquire connection asynchronously

        Yields:
            Database connection
        """
        loop = asyncio.get_event_loop()

        # Acquire connection in thread
        conn = await loop.run_in_executor(
            self._executor,
            self.pool._pool.get,
            True,
            self.pool.timeout
        )

        try:
            yield conn
        finally:
            # Return connection in thread
            await loop.run_in_executor(
                self._executor,
                self.pool._pool.put,
                conn
            )

    async def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.pool.get_stats
        )


# Global connection pool instance
_connection_pool: Optional[ConnectionPool] = None
_async_pool: Optional[AsyncDatabasePool] = None


def get_connection_pool() -> ConnectionPool:
    """Get or create global connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool(
            min_size=5,
            max_size=20,
            timeout=30.0
        )
    return _connection_pool


async def get_async_pool() -> AsyncDatabasePool:
    """Get or create global async pool"""
    global _async_pool
    if _async_pool is None:
        _async_pool = AsyncDatabasePool(get_connection_pool())
        await _async_pool.initialize()
    return _async_pool


# Convenience functions for backward compatibility
def execute_query(query: str, params: tuple = None) -> List[Any]:
    """Execute query using global pool"""
    pool = get_connection_pool()
    return pool.execute(query, params)


async def execute_query_async(query: str, params: tuple = None) -> List[Any]:
    """Execute query asynchronously using global pool"""
    pool = await get_async_pool()
    return await pool.execute(query, params)


# Connection pool monitoring
class PoolMonitor:
    """Monitor connection pool health and performance"""

    def __init__(self, pool: ConnectionPool):
        self.pool = pool
        self.monitoring = False
        self._monitor_thread = None

    def start_monitoring(self, interval: int = 60):
        """Start monitoring thread"""
        self.monitoring = True
        self._monitor_thread = Thread(target=self._monitor_loop, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        """Monitoring loop"""
        while self.monitoring:
            stats = self.pool.get_stats()

            # Log statistics
            logger.info(f"Connection Pool Stats: {stats}")

            # Check for issues
            if stats['active_connections'] > self.pool.max_size * 0.8:
                logger.warning(f"High connection usage: {stats['active_connections']}/{self.pool.max_size}")

            if stats['pool_exhausted_count'] > 0:
                logger.warning(f"Pool exhausted {stats['pool_exhausted_count']} times")

            if stats['avg_wait_time'] > 1.0:
                logger.warning(f"High average wait time: {stats['avg_wait_time']:.2f}s")

            time.sleep(interval)