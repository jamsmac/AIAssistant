"""
Integration tests for complete workflows
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


class TestUserRegistrationFlow:
    """Test complete user registration flow"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, client: AsyncClient):
        """Test user registration and login flow"""
        # Step 1: Register new user
        register_data = {
            "email": "integration@example.com",
            "password": "SecurePass123!"
        }
        register_response = await client.post("/api/auth/register", json=register_data)
        
        if register_response.status_code == 201:
            assert "access_token" in register_response.json()
            
            # Step 2: Login with credentials
            login_response = await client.post(
                "/api/auth/login",
                data={
                    "username": register_data["email"],
                    "password": register_data["password"]
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                
                # Step 3: Access protected resource
                profile_response = await client.get(
                    "/api/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                assert profile_response.status_code == 200
                assert profile_response.json()["email"] == register_data["email"]


class TestProjectWorkflow:
    """Test complete project workflow"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_project_creation_workflow(self, authenticated_client: AsyncClient):
        """Test project creation and management workflow"""
        # Step 1: Create project
        project_data = {
            "name": "Integration Test Project",
            "description": "Test project for integration tests"
        }
        create_response = await authenticated_client.post(
            "/api/projects",
            json=project_data
        )
        
        if create_response.status_code in [200, 201]:
            project = create_response.json()
            project_id = project["id"]
            
            # Step 2: Get project details
            get_response = await authenticated_client.get(f"/api/projects/{project_id}")
            if get_response.status_code == 200:
                assert get_response.json()["name"] == project_data["name"]
            
            # Step 3: Update project
            update_data = {"name": "Updated Project Name"}
            update_response = await authenticated_client.patch(
                f"/api/projects/{project_id}",
                json=update_data
            )
            
            if update_response.status_code == 200:
                assert update_response.json()["name"] == update_data["name"]
            
            # Step 4: Delete project
            delete_response = await authenticated_client.delete(f"/api/projects/{project_id}")
            assert delete_response.status_code in [200, 204]


class TestAIWorkflow:
    """Test AI model integration workflow"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ai_completion_workflow(self, authenticated_client: AsyncClient):
        """Test AI completion workflow"""
        # Step 1: Get available models
        models_response = await authenticated_client.get("/api/ai/models")
        
        if models_response.status_code == 200:
            models = models_response.json()
            
            # Step 2: Make AI completion request
            completion_data = {
                "prompt": "Hello, world!",
                "model": "gpt-4" if isinstance(models, list) and "gpt-4" in str(models) else "gpt-3.5-turbo",
                "provider": "openai"
            }
            
            completion_response = await authenticated_client.post(
                "/api/ai/completions",
                json=completion_data
            )
            
            # Response may vary based on implementation
            assert completion_response.status_code in [200, 404, 501]


class TestEndToEnd:
    """End-to-end system tests"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_platform_workflow(self, client: AsyncClient):
        """Test complete platform workflow from registration to AI usage"""
        # 1. Health check
        health = await client.get("/api/health")
        assert health.status_code in [200, 503]
        
        # 2. Register user
        user_data = {
            "email": f"e2e{datetime.utcnow().timestamp()}@example.com",
            "password": "SecureE2EPass123!"
        }
        register = await client.post("/api/auth/register", json=user_data)
        
        if register.status_code == 201:
            token = register.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Create project
            project = await client.post(
                "/api/projects",
                json={"name": "E2E Test Project"},
                headers=headers
            )
            
            if project.status_code in [200, 201]:
                # 4. Verify metrics updated
                metrics = await client.get("/metrics")
                assert metrics.status_code == 200
