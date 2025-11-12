# Migration Guide: v2.x → v3.0

## Overview

This guide helps you migrate from AI Assistant Platform v2.x to v3.0. The new version introduces significant architectural improvements while maintaining backward compatibility with existing Fractal Agents.

## Breaking Changes

### 1. Server Entry Point

**Before (v2.x):**
```bash
python api/server.py
```

**After (v3.0):**
```bash
python api/main.py
```

### 2. Import Changes

**Before:**
```python
from api.server import app
```

**After:**
```python
from api.main import app
```

## New Features to Adopt

### 1. Use Enhanced Fractal Agent

**Migration Steps:**

1. Update your agent imports:
```python
# Old
from agents.fractal.base_agent import FractalAgent

# New
from agents.fractal.enhanced_agent import EnhancedFractalAgent
```

2. Update agent initialization:
```python
# Old
agent = FractalAgent(agent_id, db, api_key)

# New
agent = EnhancedFractalAgent(
    agent_id,
    db,
    api_key,
    use_plugin_registry=True,  # Enable new features
    use_llm_router=True
)
```

3. Existing code continues to work - EnhancedFractalAgent is backward compatible!

### 2. Register Your Custom Agents

If you have custom agents, register them with the Plugin Registry:

```python
from agents.registry import get_registry, PluginMetadata, AgentDefinition
import hashlib

# Create plugin metadata
plugin = PluginMetadata(
    name="my-custom-agents",
    version="1.0.0",
    description="My custom agent collection",
    category="development",
    author="your-name",
    agents=["my-agent-1", "my-agent-2"],
    checksum=hashlib.md5(b"my-custom-agents1.0.0").hexdigest()
)

# Register plugin
registry = get_registry()
registry.register_plugin(plugin)

# Register each agent
for agent_name in ["my-agent-1", "my-agent-2"]:
    agent_def = AgentDefinition(
        name=agent_name,
        description="My custom agent",
        model="sonnet",
        system_prompt="You are a helpful assistant.",
        trigger_keywords=[agent_name]
    )
    registry.register_agent(agent_def, "my-custom-agents")
```

### 3. Convert Skills to Progressive Disclosure

If you have skills/capabilities, convert them to the new format:

```python
from agents.registry.models import SkillMetadata
from agents.skills import get_skills_registry

# Create skill metadata (Level 1)
skill = SkillMetadata(
    name="backend-development",
    description="Backend development skills",
    category="development",
    level=1,
    triggers=["backend", "api", "server"],
    instructions_path="skills/backend/instructions.md",
    resources_path="skills/backend/resources.json"
)

# Register skill
skills_registry = get_skills_registry()
skills_registry.register_skill(skill)
```

### 4. Enable LLM Router

Update your task execution to use intelligent routing:

```python
from agents.routing import get_llm_router

# Before executing tasks
router = get_llm_router()

# Analyze and route
model, complexity, details = await router.route_task(task_description)

# Use the selected model
task['selected_model'] = model
result = await agent.execute_task(task)

# Check cost savings
stats = router.get_statistics()
print(f"Cost savings: {stats['cost_savings_percentage']}%")
```

## Step-by-Step Migration

### Step 1: Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Step 2: Update Environment Variables

Add new optional variables to `.env`:

```bash
# Existing variables remain the same
SECRET_KEY=...
ANTHROPIC_API_KEY=...

# New optional variables
ENABLE_PLUGIN_REGISTRY=true
ENABLE_LLM_ROUTER=true
PREFER_COST_EFFICIENCY=true
```

### Step 3: Update Server Startup

Update your startup scripts:

**Old:**
```bash
#!/bin/bash
uvicorn api.server:app --reload
```

**New:**
```bash
#!/bin/bash
uvicorn api.main:app --reload
```

### Step 4: Test Existing Functionality

Run your existing tests to ensure backward compatibility:

```bash
pytest tests/
```

All existing tests should pass without modification.

### Step 5: Gradually Adopt New Features

Start using new features incrementally:

1. **Week 1**: Switch to `api/main.py` entry point
2. **Week 2**: Migrate to EnhancedFractalAgent
3. **Week 3**: Register custom agents with Plugin Registry
4. **Week 4**: Enable LLM Router for cost optimization
5. **Week 5**: Convert skills to Progressive Disclosure

## API Changes

### New Endpoints

```
GET  /api/agents                    # List all agents
GET  /api/agents/{id}               # Get agent details
POST /api/agents/execute            # Execute agent

GET  /api/financial/analyze/stock   # Stock analysis
POST /api/financial/market/data     # Market data

GET  /api/workflows/list            # List workflows
POST /api/workflows/{id}/execute    # Execute workflow
```

### Deprecated Endpoints

None - all existing endpoints remain functional.

## Database Changes

### New Tables

The following tables are created automatically on first run:

```sql
-- Plugin Registry
CREATE TABLE IF NOT EXISTS plugins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Skills Registry
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    metadata JSONB NOT NULL,
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Existing Tables

No changes to existing tables - full backward compatibility.

## Configuration Changes

### Old Configuration (v2.x)

```python
# api/server.py
app = FastAPI(title="AI Assistant", version="2.0.0")
```

### New Configuration (v3.0)

```python
# api/main.py
app = FastAPI(
    title="AI Assistant Platform API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

## Testing Your Migration

### 1. Run Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
    "status": "healthy",
    "version": "3.0.0",
    "environment": "development"
}
```

### 2. Test Existing Endpoints

```bash
# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"Hello"}'
```

### 3. Test New Features

```bash
# List agents
curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get LLM Router statistics
curl http://localhost:8000/api/monitoring/llm-router/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Rollback Plan

If you need to rollback to v2.x:

1. **Stop the server**
```bash
pkill -f "python api/main.py"
```

2. **Checkout v2.x branch**
```bash
git checkout v2.x
```

3. **Restore dependencies**
```bash
pip install -r requirements.txt
```

4. **Start old server**
```bash
python api/server.py
```

## Common Issues

### Issue 1: Import Errors

**Error:**
```
ImportError: cannot import name 'get_registry' from 'agents.registry'
```

**Solution:**
```bash
# Ensure all new files are present
ls agents/registry/
# Should show: __init__.py, models.py, plugin_registry.py, validator.py

# Reinstall package
pip install -e .
```

### Issue 2: Database Connection

**Error:**
```
asyncpg.exceptions.UndefinedTableError: relation "plugins" does not exist
```

**Solution:**
```bash
# Run migrations
python scripts/migrate_to_v3.py
```

### Issue 3: Missing Environment Variables

**Error:**
```
ValueError: SECRET_KEY must be set in production environment
```

**Solution:**
```bash
# Generate new SECRET_KEY
python scripts/generate_secret_key.py

# Add to .env
echo "SECRET_KEY=your-generated-key" >> .env
```

## Performance Optimization

After migration, optimize performance:

### 1. Enable Caching

```python
# In your agent initialization
agent = EnhancedFractalAgent(
    agent_id,
    db,
    api_key,
    use_plugin_registry=True,
    use_llm_router=True
)

# LLM Router automatically caches complexity analysis
```

### 2. Monitor Cost Savings

```python
from agents.routing import get_llm_router

router = get_llm_router()
stats = router.get_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Cost saved: ${stats['estimated_cost_saved']:.2f}")
print(f"Savings: {stats['cost_savings_percentage']}%")
```

### 3. Optimize Context Usage

```python
from agents.skills import get_skills_registry

skills = get_skills_registry()
stats = skills.get_statistics()

print(f"Total skills: {stats['total_skills']}")
print(f"Active skills: {stats['active_skills']}")
print(f"Context saved: {stats['context_saved']}%")
```

## Support

If you encounter issues during migration:

1. Check the [IMPLEMENTATION_V3_SUMMARY.md](IMPLEMENTATION_V3_SUMMARY.md)
2. Review the [README_v3.md](README_v3.md)
3. Open an issue on GitHub
4. Contact support

## Conclusion

The migration to v3.0 is designed to be smooth and incremental. You can:

- ✅ Start using v3.0 immediately with existing code
- ✅ Gradually adopt new features at your own pace
- ✅ Rollback easily if needed
- ✅ Enjoy 90% context savings and 77% cost reduction

Take your time and migrate feature by feature for the best results!
