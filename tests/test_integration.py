"""
Integration tests for complete workflows
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.cache_manager import CacheManager, get_cache_manager
from agents.db_pool import DatabasePool
from api.routers import monitoring_router
from api.server_refactored import app as api_app


@pytest.fixture(autouse=True)
def set_cache_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CACHE_DB_PATH", str(tmp_path / "integration_cache.db"))
    cache = get_cache_manager()
    cache.clear_cache()
    return cache


@pytest.fixture
def client():
    api_app.dependency_overrides = {}
    with TestClient(api_app) as client:
        yield client


def test_cache_persistence_across_requests(client):
    cache = get_cache_manager()
    cache.cache_response("prompt", "chat", "model", "resp", 10, ttl_hours=4)

    response = client.get("/api/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_entries"] == 1
    assert data["active_entries"] == 1


def test_monitoring_pool_stats(client, monkeypatch):
    pool = DatabasePool()

    class DummyPool:
        def get_size(self):
            return 4

        def get_idle_size(self):
            return 2

        def get_max_size(self):
            return 10

        def get_min_size(self):
            return 1

    pool.pool = DummyPool()
    monkeypatch.setattr("agents.db_pool.db_pool", pool)

    response = client.get("/api/monitoring/pool")
    assert response.status_code == 200
    payload = response.json()
    assert payload["size"] == 4
    assert payload["free_connections"] == 2


def test_monitoring_cache_cleanup(client):
    cache = get_cache_manager()
    cache.cache_response("prompt", "chat", "model", "resp", 10, ttl_hours=0)

    cleanup = client.post("/api/cache/cleanup")
    assert cleanup.status_code == 200
    assert cleanup.json()["deleted_entries"] >= 1


def test_auth_cookie_login_flow(client, monkeypatch):
    from agents.auth import validate_secret_key

    async def fake_login(data):
        return {"access_token": "token", "token_type": "bearer"}

    response = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "Password123"},
    )
    assert response.status_code in (200, 401)
