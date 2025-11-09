import os
import sys
import importlib
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def monitoring_client(tmp_path, monkeypatch):
    cache_path = tmp_path / "cache.db"
    monkeypatch.setenv("CACHE_DB_PATH", str(cache_path))

    for module in ["api.routers.monitoring_router", "agents.cache_manager"]:
        sys.modules.pop(module, None)

    cache_manager = importlib.import_module("agents.cache_manager")
    importlib.reload(cache_manager)

    monitoring_router = importlib.import_module("api.routers.monitoring_router")
    importlib.reload(monitoring_router)

    app = FastAPI()
    app.include_router(monitoring_router.router)

    client = TestClient(app)
    client.cache_manager = cache_manager.get_cache_manager(str(cache_path))  # type: ignore[attr-defined]
    return client


def test_cache_stats_endpoint(monitoring_client):
    response = monitoring_client.get("/api/cache/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_entries"] == 0
    assert payload["expired_entries"] == 0
    assert payload["active_entries"] == 0


def test_cache_cleanup_endpoint(monitoring_client):
    cache_manager = monitoring_client.cache_manager
    cache_manager.cache_response("prompt", "chat", "gemini", "response", 5, ttl_hours=1)

    # Force expiration
    with cache_manager._connect() as conn:  # type: ignore[attr-defined]
        conn.execute(
            "UPDATE cache SET expires_at = datetime('now', '-2 hours')"
        )
        conn.commit()

    cleanup_response = monitoring_client.post("/api/cache/cleanup")
    assert cleanup_response.status_code == 200
    assert cleanup_response.json()["deleted_entries"] == 1

    stats_response = monitoring_client.get("/api/cache/stats")
    assert stats_response.json()["total_entries"] == 0
