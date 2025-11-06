"""
Global test fixtures and configuration
"""
import pytest
import asyncio
import os


# Set test environment
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)
