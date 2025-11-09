"""Cache manager for AI responses with SQLite backend."""
from __future__ import annotations

import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import os

logger = logging.getLogger(__name__)


class CacheManager:
    """Persistent cache for AI responses."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_cache_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def _init_cache_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    prompt_hash TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    tokens_used INTEGER,
                    cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    last_accessed TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash ON cache(prompt_hash)")
            conn.commit()

    def generate_cache_key(self, prompt: str, task_type: str, model_name: str) -> str:
        content = f"{prompt}|{task_type}|{model_name}"
        return hashlib.md5(content.encode()).hexdigest()

    def _prompt_hash(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def get_cached_response(
        self,
        prompt: str,
        task_type: str,
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        cache_key = self.generate_cache_key(prompt, task_type, model_name)
        now = datetime.utcnow()

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT response, tokens_used, cached_at, expires_at, hit_count
                FROM cache
                WHERE cache_key = ? AND expires_at > ?
                LIMIT 1
                """,
                (cache_key, now.isoformat()),
            )
            row = cursor.fetchone()

            if not row:
                return None

            conn.execute(
                """
                UPDATE cache
                SET hit_count = hit_count + 1,
                    last_accessed = ?
                WHERE cache_key = ?
                """,
                (now.isoformat(), cache_key),
            )
            conn.commit()

            return {
                "response": row["response"],
                "tokens_used": row["tokens_used"] or 0,
                "cached_at": row["cached_at"],
                "expires_at": row["expires_at"],
                "hit_count": row["hit_count"] + 1,
            }

    def cache_response(
        self,
        prompt: str,
        task_type: str,
        model_name: str,
        response: str,
        tokens_used: int,
        ttl_hours: Optional[int] = None
    ) -> None:
        cache_key = self.generate_cache_key(prompt, task_type, model_name)
        prompt_hash = self._prompt_hash(prompt)

        ttl_map = {
            "conversation": 1,
            "chat": 1,
            "code": 24,
            "analysis": 168,
            "translation": 720,
            "general": 24,
        }
        ttl = ttl_hours if ttl_hours is not None else ttl_map.get(task_type, 24)
        expires_at = datetime.utcnow() + timedelta(hours=ttl)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                    (cache_key, prompt_hash, task_type, model_name, response, tokens_used, expires_at, cached_at, hit_count, last_accessed)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT cached_at FROM cache WHERE cache_key = ?), CURRENT_TIMESTAMP),
                     COALESCE((SELECT hit_count FROM cache WHERE cache_key = ?), 0),
                     CURRENT_TIMESTAMP)
                """,
                (
                    cache_key,
                    prompt_hash,
                    task_type,
                    model_name,
                    response,
                    tokens_used,
                    expires_at.isoformat(),
                    cache_key,
                    cache_key,
                ),
            )
            conn.commit()

    def cleanup_expired(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),),
            )
            deleted = cursor.rowcount or 0
            conn.commit()
            if deleted:
                logger.info("Cache cleanup removed %s entries", deleted)
            return deleted

    def clear_cache(self, task_type: Optional[str] = None) -> int:
        with self._connect() as conn:
            if task_type:
                cursor = conn.execute("DELETE FROM cache WHERE task_type = ?", (task_type,))
            else:
                cursor = conn.execute("DELETE FROM cache")
            deleted = cursor.rowcount or 0
            conn.commit()
            logger.info("Cleared %s cache entries (task_type=%s)", deleted, task_type or "all")
            return deleted

    def get_cache_stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            total = conn.execute("SELECT COUNT(*) as cnt FROM cache").fetchone()["cnt"]
            expired = conn.execute(
                "SELECT COUNT(*) as cnt FROM cache WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),),
            ).fetchone()["cnt"]
            total_hits = conn.execute("SELECT SUM(hit_count) FROM cache").fetchone()[0] or 0
            top_rows = conn.execute(
                """
                SELECT task_type, model_name, hit_count
                FROM cache
                ORDER BY hit_count DESC
                LIMIT 5
                """
            ).fetchall()

            return {
                "total_entries": total,
                "active_entries": total - expired,
                "expired_entries": expired,
                "total_hits": total_hits,
                "hit_rate": (total_hits / total) if total else 0,
                "top_entries": [
                    {
                        "task_type": row["task_type"],
                        "model": row["model_name"],
                        "hits": row["hit_count"],
                    }
                    for row in top_rows
                ],
            }


_default_cache_path = Path(__file__).parent.parent / "data" / "autopilot_cache.db"
_default_cache_path.parent.mkdir(parents=True, exist_ok=True)
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(db_path: Optional[str] = None) -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        path = db_path or os.getenv("CACHE_DB_PATH") or str(_default_cache_path)
        _cache_manager = CacheManager(path)
    return _cache_manager
