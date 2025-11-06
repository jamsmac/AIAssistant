# Testing Guide

## Overview

This project maintains >80% test coverage with comprehensive unit, integration, and end-to-end tests.

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── test_auth.py             # Authentication tests
├── test_api_endpoints.py    # API endpoint tests
├── test_database.py         # Database operation tests
├── test_health_checks.py    # Health monitoring tests
├── test_integration.py      # Integration tests
└── test_performance.py      # Performance and load tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test class
pytest tests/test_auth.py::TestPasswordHashing

# Run specific test
pytest tests/test_auth.py::TestPasswordHashing::test_password_hash
```

### Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# End-to-end tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"

# Critical path tests
pytest -m critical
```

### Using the Test Script

```bash
# Run comprehensive test suite with coverage
./scripts/run_tests.sh
```

This will:
- Install test dependencies
- Run all tests with coverage
- Generate HTML, JSON, and terminal coverage reports
- Create coverage badge
- Verify 80% coverage threshold

## Test Fixtures

### Database Fixtures

```python
# Use test database session
async def test_something(test_session):
    user = User(email="test@example.com")
    test_session.add(user)
    await test_session.commit()
```

### HTTP Client Fixtures

```python
# Unauthenticated client
async def test_endpoint(client):
    response = await client.get("/api/health")
    assert response.status_code == 200

# Authenticated client
async def test_protected(authenticated_client):
    response = await authenticated_client.get("/api/projects")
    assert response.status_code == 200
```

### Mock Fixtures

```python
# Mock external services
async def test_ai(mock_openai):
    # OpenAI calls are automatically mocked
    response = await make_ai_request()
    assert response is not None
```

## Writing Tests

### Test Structure

```python
import pytest
from httpx import AsyncClient


class TestFeature:
    """Test feature description"""

    @pytest.mark.asyncio
    async def test_something(self, client: AsyncClient):
        """Test specific behavior"""
        # Arrange
        data = {"key": "value"}

        # Act
        response = await client.post("/api/endpoint", json=data)

        # Assert
        assert response.status_code == 200
        assert response.json()["key"] == "value"
```

### Test Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.slow         # Test takes >5 seconds
@pytest.mark.smoke        # Quick smoke test
@pytest.mark.critical     # Critical path test
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation(test_session):
    result = await async_function()
    assert result is not None
```

## Coverage Requirements

- **Minimum coverage**: 80%
- **Target coverage**: 90%
- **Critical modules**: 95%

### Checking Coverage

```bash
# Generate HTML coverage report
pytest --cov=api --cov-report=html
open htmlcov/index.html

# Terminal coverage report
pytest --cov=api --cov-report=term-missing

# JSON coverage report
pytest --cov=api --cov-report=json
cat coverage.json
```

### Excluded from Coverage

- Test files
- Migrations
- Virtual environments
- `__pycache__`
- Abstract methods
- Type checking blocks

## Continuous Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests

### CI Pipeline

1. **Unit Tests** (Python 3.11, 3.12)
   - Install dependencies
   - Run tests with coverage
   - Upload to Codecov
   - Check 80% threshold

2. **Integration Tests**
   - Start PostgreSQL and Redis
   - Run integration tests
   - Verify external service integration

3. **Security Scan**
   - Snyk vulnerability scan
   - Bandit security analysis

## Performance Testing

### Load Tests

```bash
# Run performance tests
pytest tests/test_performance.py -v

# Test specific performance aspect
pytest tests/test_performance.py::TestPerformance::test_response_time
```

### Benchmarking

```python
@pytest.mark.slow
@pytest.mark.asyncio
async def test_benchmark(client):
    start = time.time()
    response = await client.get("/api/endpoint")
    duration = time.time() - start

    assert duration < 1.0  # Should respond within 1 second
```

## Mocking External Services

### OpenAI

```python
async def test_with_openai(mock_openai):
    # Automatically mocked
    response = await call_openai_api()
    assert response is not None
```

### Database

```python
async def test_with_db(test_session):
    # Uses in-memory SQLite
    user = User(email="test@example.com")
    test_session.add(user)
    await test_session.commit()
```

### Redis

```python
async def test_with_redis(redis_client):
    # Uses test Redis database (db 1)
    await redis_client.set("key", "value")
    value = await redis_client.get("key")
    assert value == "value"
```

## Troubleshooting

### Common Issues

1. **Import errors**
   ```bash
   # Ensure PYTHONPATH includes project root
   export PYTHONPATH=/path/to/project:$PYTHONPATH
   ```

2. **Async test failures**
   ```python
   # Always use @pytest.mark.asyncio decorator
   @pytest.mark.asyncio
   async def test_async():
       pass
   ```

3. **Database connection errors**
   ```bash
   # Check test database URL
   export DATABASE_URL="sqlite+aiosqlite:///:memory:"
   ```

4. **Fixture not found**
   ```python
   # Fixtures are defined in conftest.py
   # Make sure conftest.py is in tests/ directory
   ```

### Debug Mode

```bash
# Run with verbose output
pytest -vv

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Speed**: Unit tests should be fast (<100ms)
3. **Coverage**: Aim for >80% coverage
4. **Clarity**: Test names should describe what they test
5. **Arrange-Act-Assert**: Follow AAA pattern
6. **Mocking**: Mock external services and APIs
7. **Cleanup**: Use fixtures for setup and teardown
8. **Async**: Use `@pytest.mark.asyncio` for async tests

## Test Coverage Report

Current coverage status is tracked in:
- HTML: `htmlcov/index.html`
- JSON: `coverage.json`
- Badge: `coverage.svg`

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
