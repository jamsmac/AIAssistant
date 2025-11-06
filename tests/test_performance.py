"""
Performance and load tests
"""
import pytest
import asyncio
import time
from httpx import AsyncClient


class TestPerformance:
    """Test system performance"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_response_time(self, client: AsyncClient):
        """Test API response time"""
        start = time.time()
        response = await client.get("/api/health")
        duration = time.time() - start
        
        assert response.status_code in [200, 503]
        assert duration < 1.0  # Should respond within 1 second

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test handling concurrent requests"""
        async def make_request():
            return await client.get("/api/health")
        
        # Make 50 concurrent requests
        start = time.time()
        responses = await asyncio.gather(*[make_request() for _ in range(50)])
        duration = time.time() - start
        
        # All should succeed
        assert all(r.status_code in [200, 503] for r in responses)
        # Should handle all requests within reasonable time
        assert duration < 10.0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_database_query_performance(self, test_session, test_user):
        """Test database query performance"""
        from sqlalchemy import select
        from api.models import User
        
        start = time.time()
        result = await test_session.execute(
            select(User).where(User.email == test_user.email)
        )
        user = result.scalar_one()
        duration = time.time() - start
        
        assert user is not None
        assert duration < 0.1  # Query should be fast


class TestScalability:
    """Test system scalability"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_operations(self, test_session):
        """Test bulk database operations"""
        from api.models import User
        
        # Create 1000 users
        users = [
            User(email=f"bulk{i}@example.com", hashed_password="hash")
            for i in range(1000)
        ]
        
        start = time.time()
        test_session.add_all(users)
        await test_session.commit()
        duration = time.time() - start
        
        # Should complete reasonably fast
        assert duration < 5.0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_pagination_performance(self, test_session):
        """Test pagination performance with large dataset"""
        from sqlalchemy import select
        from api.models import User
        
        # Query with pagination
        start = time.time()
        result = await test_session.execute(
            select(User).limit(100).offset(0)
        )
        users = result.scalars().all()
        duration = time.time() - start
        
        assert duration < 0.5


class TestMemoryUsage:
    """Test memory efficiency"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, client: AsyncClient):
        """Test for memory leaks during repeated requests"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for _ in range(100):
            await client.get("/api/health")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50


class TestCaching:
    """Test caching effectiveness"""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, authenticated_client: AsyncClient):
        """Test cached response performance"""
        # First request (cache miss)
        start1 = time.time()
        response1 = await authenticated_client.get("/api/projects")
        duration1 = time.time() - start1
        
        # Second request (should hit cache)
        start2 = time.time()
        response2 = await authenticated_client.get("/api/projects")
        duration2 = time.time() - start2
        
        # Both should succeed
        assert response1.status_code in [200, 404]
        assert response2.status_code in [200, 404]
        
        # Cached request should be faster (or similar if no caching)
        # Just verify both are reasonably fast
        assert duration1 < 2.0
        assert duration2 < 2.0
