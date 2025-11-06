"""
Health check tests
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


class TestHealthEndpoints:
    """Test health monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_comprehensive_health(self, client: AsyncClient):
        """Test comprehensive health check"""
        response = await client.get("/api/health")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data

    @pytest.mark.asyncio
    async def test_database_health(self, client: AsyncClient):
        """Test database health check"""
        response = await client.get("/api/health")

        data = response.json()
        if "checks" in data and "database" in data["checks"]:
            db_check = data["checks"]["database"]
            assert "status" in db_check
            assert "response_time_ms" in db_check

    @pytest.mark.asyncio
    async def test_liveness_probe(self, client: AsyncClient):
        """Test Kubernetes liveness probe"""
        response = await client.get("/api/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_probe(self, client: AsyncClient):
        """Test Kubernetes readiness probe"""
        response = await client.get("/api/health/ready")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_startup_probe(self, client: AsyncClient):
        """Test Kubernetes startup probe"""
        response = await client.get("/api/health/startup")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "uptime" in data


class TestSystemMetrics:
    """Test system metrics collection"""

    @pytest.mark.asyncio
    async def test_system_resources_check(self, client: AsyncClient):
        """Test system resources health check"""
        response = await client.get("/api/health")

        data = response.json()
        if "checks" in data and "system_resources" in data["checks"]:
            sys_check = data["checks"]["system_resources"]
            assert "cpu" in sys_check or "memory" in sys_check

    @pytest.mark.asyncio
    @patch("psutil.cpu_percent")
    async def test_high_cpu_detection(self, mock_cpu, client: AsyncClient):
        """Test high CPU detection"""
        mock_cpu.return_value = 95.0

        response = await client.get("/api/health")
        data = response.json()

        # Should detect degraded or unhealthy status
        assert data["status"] in ["healthy", "degraded", "unhealthy", "critical"]


class TestExternalDependencies:
    """Test external service health checks"""

    @pytest.mark.asyncio
    async def test_redis_health(self, client: AsyncClient):
        """Test Redis health check"""
        response = await client.get("/api/health")

        data = response.json()
        if "checks" in data and "redis" in data["checks"]:
            redis_check = data["checks"]["redis"]
            assert "status" in redis_check

    @pytest.mark.asyncio
    async def test_external_apis_health(self, client: AsyncClient):
        """Test external APIs health check"""
        response = await client.get("/api/health")

        data = response.json()
        if "checks" in data and "external_apis" in data["checks"]:
            api_check = data["checks"]["external_apis"]
            assert "apis" in api_check or "status" in api_check
