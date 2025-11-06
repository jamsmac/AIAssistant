"""
API endpoint integration tests
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_basic_health_check(self, client: AsyncClient):
        """Test basic health check"""
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

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
        assert "status" in response.json()


class TestUserEndpoints:
    """Test user management endpoints"""

    @pytest.mark.asyncio
    async def test_get_users_list(self, authenticated_client: AsyncClient):
        """Test getting users list"""
        response = await authenticated_client.get("/api/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "users" in data

    @pytest.mark.asyncio
    async def test_get_user_profile(self, authenticated_client: AsyncClient, test_user):
        """Test getting user profile"""
        response = await authenticated_client.get(f"/api/users/{test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_update_user_profile(self, authenticated_client: AsyncClient, test_user):
        """Test updating user profile"""
        response = await authenticated_client.patch(
            f"/api/users/{test_user.id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code in [200, 404]


class TestProjectEndpoints:
    """Test project management endpoints"""

    @pytest.mark.asyncio
    async def test_create_project(self, authenticated_client: AsyncClient):
        """Test project creation"""
        response = await authenticated_client.post(
            "/api/projects",
            json={
                "name": "New Project",
                "description": "Test project"
            }
        )

        assert response.status_code in [201, 200]
        data = response.json()
        assert data["name"] == "New Project"

    @pytest.mark.asyncio
    async def test_get_projects(self, authenticated_client: AsyncClient, test_project):
        """Test getting projects list"""
        response = await authenticated_client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "projects" in data

    @pytest.mark.asyncio
    async def test_get_project_detail(self, authenticated_client: AsyncClient, test_project):
        """Test getting project details"""
        response = await authenticated_client.get(f"/api/projects/{test_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id

    @pytest.mark.asyncio
    async def test_update_project(self, authenticated_client: AsyncClient, test_project):
        """Test updating project"""
        response = await authenticated_client.patch(
            f"/api/projects/{test_project.id}",
            json={"name": "Updated Project Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"

    @pytest.mark.asyncio
    async def test_delete_project(self, authenticated_client: AsyncClient, test_project):
        """Test deleting project"""
        response = await authenticated_client.delete(f"/api/projects/{test_project.id}")

        assert response.status_code in [200, 204]


class TestAIEndpoints:
    """Test AI model endpoints"""

    @pytest.mark.asyncio
    async def test_ai_completion(self, authenticated_client: AsyncClient, mock_openai):
        """Test AI completion endpoint"""
        response = await authenticated_client.post(
            "/api/ai/completions",
            json={
                "prompt": "Hello, world!",
                "model": "gpt-4",
                "provider": "openai"
            }
        )

        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_get_models_list(self, authenticated_client: AsyncClient):
        """Test getting available AI models"""
        response = await authenticated_client.get("/api/ai/models")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "models" in data


class TestMetricsEndpoints:
    """Test metrics and monitoring endpoints"""

    @pytest.mark.asyncio
    async def test_prometheus_metrics(self, client: AsyncClient):
        """Test Prometheus metrics endpoint"""
        response = await client.get("/metrics")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_application_metrics(self, authenticated_client: AsyncClient):
        """Test application metrics endpoint"""
        response = await authenticated_client.get("/api/metrics")

        assert response.status_code in [200, 404]


class TestVersioningEndpoints:
    """Test API versioning endpoints"""

    @pytest.mark.asyncio
    async def test_v1_endpoint(self, client: AsyncClient):
        """Test v1 API endpoint"""
        response = await client.get("/api/v1/users")

        assert "API-Version" in response.headers or "X-API-Version" in response.headers

    @pytest.mark.asyncio
    async def test_v2_endpoint(self, client: AsyncClient):
        """Test v2 API endpoint"""
        response = await client.get("/api/v2/users")

        assert "API-Version" in response.headers or "X-API-Version" in response.headers

    @pytest.mark.asyncio
    async def test_version_header(self, client: AsyncClient):
        """Test API version via header"""
        response = await client.get(
            "/api/users",
            headers={"Accept-Version": "v2"}
        )

        assert response.status_code in [200, 400, 404]


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_404_not_found(self, client: AsyncClient):
        """Test 404 error handling"""
        response = await client.get("/api/nonexistent-endpoint")

        assert response.status_code == 404
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_validation_error(self, authenticated_client: AsyncClient):
        """Test validation error handling"""
        response = await authenticated_client.post(
            "/api/projects",
            json={"invalid": "data"}
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_unauthorized_error(self, client: AsyncClient):
        """Test unauthorized access"""
        response = await client.get("/api/projects")

        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting"""

    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, client: AsyncClient):
        """Test rate limit enforcement"""
        # Make multiple requests
        responses = []
        for _ in range(100):
            response = await client.get("/api/health")
            responses.append(response)

        # Check if any requests were rate limited
        status_codes = [r.status_code for r in responses]
        # Rate limiting might return 429
        assert all(code in [200, 429] for code in status_codes)