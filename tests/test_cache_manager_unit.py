import sqlite3
from datetime import datetime, timedelta

from agents.cache_manager import CacheManager


def create_cache(tmp_path) -> CacheManager:
    db_path = tmp_path / "cache.db"
    return CacheManager(str(db_path))


def test_cache_store_and_retrieve(tmp_path):
    cache = create_cache(tmp_path)

    cache.cache_response(
        prompt="hello",
        task_type="chat",
        model_name="gpt-4",
        response="world",
        tokens_used=42,
        ttl_hours=2,
    )

    result = cache.get_cached_response("hello", "chat", "gpt-4")
    assert result is not None
    assert result["response"] == "world"
    assert result["tokens_used"] == 42
    assert result["hit_count"] == 1


def test_cache_expiration(tmp_path):
    cache = create_cache(tmp_path)
    cache.cache_response("prompt", "analysis", "claude", "answer", 10, ttl_hours=1)

    # Force expiration by setting expires_at in the past
    with cache._connect() as conn:
        conn.execute(
            "UPDATE cache SET expires_at = ?",
            ((datetime.utcnow() - timedelta(hours=2)).isoformat(),),
        )
        conn.commit()

    assert cache.get_cached_response("prompt", "analysis", "claude") is None


def test_cache_cleanup(tmp_path):
    cache = create_cache(tmp_path)
    cache.cache_response("prompt", "code", "deepseek", "answer", 5, ttl_hours=1)

    with cache._connect() as conn:
        conn.execute(
            "UPDATE cache SET expires_at = ?",
            ((datetime.utcnow() - timedelta(hours=3)).isoformat(),),
        )
        conn.commit()

    deleted = cache.cleanup_expired()
    assert deleted == 1
    assert cache.get_cached_response("prompt", "code", "deepseek") is None


def test_cache_stats(tmp_path):
    cache = create_cache(tmp_path)
    cache.cache_response("p1", "chat", "gemini", "r1", 3, ttl_hours=24)
    cache.cache_response("p2", "analysis", "claude", "r2", 5, ttl_hours=24)
    cache.get_cached_response("p1", "chat", "gemini")

    stats = cache.get_cache_stats()
    assert stats["total_entries"] == 2
    assert stats["active_entries"] == 2
    assert stats["expired_entries"] == 0
    assert stats["total_hits"] == 1
    assert stats["top_entries"][0]["task_type"] == "chat"
