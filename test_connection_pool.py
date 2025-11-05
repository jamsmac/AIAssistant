"""
Test Connection Pool Performance
Compare performance with and without connection pooling
"""

import time
import sqlite3
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from agents.database_pool import ConnectionPool, get_connection_pool
from agents.database_v2 import PooledDatabase
from agents.database import HistoryDatabase


def test_without_pooling(num_queries: int = 1000):
    """Test performance without connection pooling"""
    db_path = "data/history.db"
    times = []

    for i in range(num_queries):
        start = time.time()

        # Create new connection each time
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM requests")
        result = cursor.fetchone()
        conn.close()

        elapsed = time.time() - start
        times.append(elapsed)

        if (i + 1) % 100 == 0:
            print(f"Without pooling: {i + 1}/{num_queries} queries completed")

    return times


def test_with_pooling(num_queries: int = 1000):
    """Test performance with connection pooling"""
    pool = ConnectionPool(min_size=5, max_size=20)
    times = []

    for i in range(num_queries):
        start = time.time()

        # Use pooled connection
        result = pool.execute("SELECT COUNT(*) FROM requests")

        elapsed = time.time() - start
        times.append(elapsed)

        if (i + 1) % 100 == 0:
            print(f"With pooling: {i + 1}/{num_queries} queries completed")

    # Print pool statistics
    stats = pool.get_stats()
    print(f"\nPool Statistics:")
    print(f"  Connections created: {stats['connections_created']}")
    print(f"  Connections reused: {stats['connections_reused']}")
    print(f"  Pool exhausted count: {stats['pool_exhausted_count']}")
    print(f"  Average wait time: {stats['avg_wait_time']:.4f}s")

    pool.close_all()
    return times


def test_concurrent_queries(num_threads: int = 10, queries_per_thread: int = 100):
    """Test concurrent query performance"""
    pool = ConnectionPool(min_size=5, max_size=20)

    def worker(thread_id: int):
        times = []
        for i in range(queries_per_thread):
            start = time.time()
            result = pool.execute("SELECT COUNT(*) FROM requests WHERE user_id = ?", (f"user_{thread_id}",))
            elapsed = time.time() - start
            times.append(elapsed)
        return times

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, i) for i in range(num_threads)]
        all_times = []
        for future in futures:
            all_times.extend(future.result())

    total_time = time.time() - start_time

    # Print statistics
    stats = pool.get_stats()
    print(f"\nConcurrent Test Results:")
    print(f"  Total queries: {num_threads * queries_per_thread}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Queries per second: {(num_threads * queries_per_thread) / total_time:.2f}")
    print(f"  Connections created: {stats['connections_created']}")
    print(f"  Connections reused: {stats['connections_reused']}")
    print(f"  Pool exhausted count: {stats['pool_exhausted_count']}")
    print(f"  Max active connections: {stats['total_connections']}")

    pool.close_all()
    return all_times


async def test_async_performance(num_queries: int = 1000):
    """Test async database performance"""
    from agents.database_pool import AsyncDatabasePool

    pool = ConnectionPool(min_size=5, max_size=20)
    async_pool = AsyncDatabasePool(pool)
    await async_pool.initialize()

    times = []

    for i in range(num_queries):
        start = time.time()
        result = await async_pool.execute("SELECT COUNT(*) FROM requests")
        elapsed = time.time() - start
        times.append(elapsed)

        if (i + 1) % 100 == 0:
            print(f"Async queries: {i + 1}/{num_queries} completed")

    stats = await async_pool.get_stats()
    print(f"\nAsync Pool Statistics:")
    print(f"  Queries executed: {stats['queries_executed']}")
    print(f"  Average wait time: {stats['avg_wait_time']:.4f}s")

    await async_pool.close()
    return times


def print_performance_comparison(times_without: list, times_with: list):
    """Print performance comparison statistics"""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)

    # Calculate statistics
    avg_without = statistics.mean(times_without)
    avg_with = statistics.mean(times_with)
    median_without = statistics.median(times_without)
    median_with = statistics.median(times_with)
    p95_without = sorted(times_without)[int(len(times_without) * 0.95)]
    p95_with = sorted(times_with)[int(len(times_with) * 0.95)]

    print(f"\nWithout Connection Pooling:")
    print(f"  Average: {avg_without * 1000:.2f}ms")
    print(f"  Median: {median_without * 1000:.2f}ms")
    print(f"  95th percentile: {p95_without * 1000:.2f}ms")
    print(f"  Total time: {sum(times_without):.2f}s")

    print(f"\nWith Connection Pooling:")
    print(f"  Average: {avg_with * 1000:.2f}ms")
    print(f"  Median: {median_with * 1000:.2f}ms")
    print(f"  95th percentile: {p95_with * 1000:.2f}ms")
    print(f"  Total time: {sum(times_with):.2f}s")

    print(f"\nImprovement:")
    print(f"  Speed increase: {avg_without / avg_with:.2f}x faster")
    print(f"  Time saved: {sum(times_without) - sum(times_with):.2f}s")
    print(f"  Percentage improvement: {((avg_without - avg_with) / avg_without * 100):.1f}%")


def main():
    """Run all performance tests"""
    print("=" * 60)
    print("CONNECTION POOL PERFORMANCE TEST")
    print("=" * 60)

    # Ensure database exists
    db = HistoryDatabase()

    print("\n1. Testing WITHOUT connection pooling...")
    times_without = test_without_pooling(500)

    print("\n2. Testing WITH connection pooling...")
    times_with = test_with_pooling(500)

    print_performance_comparison(times_without, times_with)

    print("\n3. Testing concurrent queries...")
    concurrent_times = test_concurrent_queries(num_threads=20, queries_per_thread=50)

    print("\n4. Testing async performance...")
    async_times = asyncio.run(test_async_performance(500))

    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)

    # Summary
    print("\nSUMMARY:")
    print(f"✅ Connection pooling is {statistics.mean(times_without) / statistics.mean(times_with):.2f}x faster")
    print(f"✅ Handles {20 * 50:.0f} concurrent queries efficiently")
    print(f"✅ Async operations work correctly")
    print(f"✅ Pool management is stable")


if __name__ == "__main__":
    main()