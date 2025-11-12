# AI Assistant Platform v3.0 - Tests

## Overview

This directory contains comprehensive integration tests for all v3.0 components.

## Test Files

### Core Components

1. **test_plugin_registry.py** - Plugin Registry tests
   - Plugin registration and validation
   - Agent, skill, and tool registration
   - Dependency resolution
   - Conflict detection
   - Export/import functionality

2. **test_llm_router.py** - LLM Router tests
   - Complexity analysis
   - Model selection
   - Cost optimization
   - Statistics tracking
   - Performance metrics

3. **test_skills_registry.py** - Skills Registry tests
   - Progressive disclosure mechanism
   - Skill activation/deactivation
   - Trigger matching
   - Context optimization
   - Token estimation

4. **test_enhanced_agent.py** - Enhanced Fractal Agent tests
   - Integration with all v3.0 components
   - Task execution
   - Backward compatibility
   - Performance metrics

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
# From project root
pytest tests/v3/ -v

# With coverage
pytest tests/v3/ --cov=agents --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/v3/test_plugin_registry.py -v
pytest tests/v3/test_llm_router.py -v
pytest tests/v3/test_skills_registry.py -v
pytest tests/v3/test_enhanced_agent.py -v
```

### Run Specific Test Class

```bash
pytest tests/v3/test_plugin_registry.py::TestPluginRegistry -v
pytest tests/v3/test_llm_router.py::TestComplexityAnalyzer -v
```

### Run Specific Test

```bash
pytest tests/v3/test_plugin_registry.py::TestPluginRegistry::test_register_plugin -v
```

## Test Coverage

### Plugin Registry (test_plugin_registry.py)

- ✅ Plugin registration
- ✅ Duplicate detection
- ✅ Agent registration
- ✅ Skill registration
- ✅ Tool registration
- ✅ Dependency resolution
- ✅ Circular dependency detection
- ✅ Version conflict detection
- ✅ Category filtering

**Coverage:** ~95%

### LLM Router (test_llm_router.py)

- ✅ Complexity analysis (5 factors)
- ✅ Model selection by complexity
- ✅ Cost estimation
- ✅ Cost savings calculation
- ✅ User preferences
- ✅ Statistics tracking
- ✅ Model capability info

**Coverage:** ~90%

### Skills Registry (test_skills_registry.py)

- ✅ Skill registration
- ✅ Progressive disclosure (3 levels)
- ✅ Skill activation/deactivation
- ✅ Trigger matching
- ✅ Auto-activation
- ✅ Context optimization
- ✅ Token estimation
- ✅ Statistics tracking
- ✅ Category filtering

**Coverage:** ~92%

### Enhanced Fractal Agent (test_enhanced_agent.py)

- ✅ Initialization with v3.0 features
- ✅ Plugin registry integration
- ✅ LLM router integration
- ✅ Skills registry integration
- ✅ Task execution
- ✅ Cost optimization
- ✅ Backward compatibility
- ✅ Performance metrics

**Coverage:** ~85%

## Test Statistics

- **Total Test Files:** 4
- **Total Test Classes:** 20+
- **Total Test Cases:** 60+
- **Average Coverage:** ~90%

## Continuous Integration

### GitHub Actions

Add to `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/v3/ -v --cov=agents --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Mock Data

Tests use mock data to avoid external dependencies:

- **Database:** Mocked with `unittest.mock`
- **API calls:** Mocked with `AsyncMock`
- **LLM responses:** Predefined responses
- **File I/O:** In-memory operations

## Best Practices

1. **Isolation:** Each test is independent
2. **Fixtures:** Reusable test data
3. **Async Support:** Proper async/await handling
4. **Clear Names:** Descriptive test names
5. **Documentation:** Each test has docstring
6. **Coverage:** Aim for >90% coverage

## Troubleshooting

### Import Errors

```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/AIAssistant"
```

### Async Test Errors

```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

### Database Connection Errors

Tests use mocked database connections. If you see database errors, ensure mocks are properly configured.

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure >85% coverage
3. Add docstrings
4. Update this README

## Future Tests

### Planned

- [ ] End-to-end workflow tests
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Security testing
- [ ] UI component tests

### Integration Tests

- [ ] Full API integration tests
- [ ] Database migration tests
- [ ] Multi-agent workflow tests
- [ ] Real LLM API tests (optional)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

**Last Updated:** November 12, 2025  
**Test Suite Version:** 3.0.0  
**Status:** ✅ All tests passing
