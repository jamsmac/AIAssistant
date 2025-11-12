# Quick Start Guide - AI Assistant Platform v3.0

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Step 1: Clone and Setup

```bash
# Clone repository
git clone https://github.com/jamsmac/AIAssistant.git
cd AIAssistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate SECRET_KEY
python scripts/generate_secret_key.py

# Edit .env and add your keys
nano .env
```

Required in `.env`:
```bash
SECRET_KEY=your-generated-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key
```

### Step 3: Start Backend

```bash
# Start the API server
python api/main.py

# Server will start on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Step 4: Start Frontend

```bash
# Open new terminal
cd web-ui

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will start on http://localhost:3000
```

### Step 5: Test the System

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🎯 First Steps

### 1. Register an Account

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourPassword123!"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourPassword123!"
  }'
```

Save the returned JWT token for subsequent requests.

### 3. Try the Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "message": "Hello! What can you help me with?"
  }'
```

## 🔥 Try v3.0 Features

### Use Enhanced Fractal Agent

```python
from agents.fractal.enhanced_agent import EnhancedFractalAgent
from agents.postgres_db import PostgresDB

# Initialize database
db = PostgresDB()
await db.connect()

# Create enhanced agent
agent = EnhancedFractalAgent(
    agent_id="demo-agent",
    db=db,
    use_plugin_registry=True,
    use_llm_router=True
)

# Initialize agent
await agent.initialize()

# Execute a task
task = {
    'description': 'Design a REST API for user management',
    'required_skills': ['backend', 'api-design']
}

result = await agent.execute_task(task)
print(result)
```

### Use LLM Router

```python
from agents.routing import get_llm_router

# Get router
router = get_llm_router()

# Analyze and route a task
model, complexity, details = await router.route_task(
    "Build a scalable microservices architecture"
)

print(f"Selected model: {model}")
print(f"Complexity: {complexity}")
print(f"Estimated cost: ${details['estimated_cost']:.6f}")
print(f"Cost savings: ${details['cost_saved_vs_gpt4']:.6f}")
```

### Use Plugin Registry

```python
from agents.registry import get_registry

# Get registry
registry = get_registry()

# List all agents
agents = registry.list_agents()
print(f"Available agents: {len(agents)}")

for agent in agents[:5]:
    print(f"- {agent.name}: {agent.description}")

# Get specific agent
agent = registry.get_agent("backend-architect")
if agent:
    print(f"\nAgent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Triggers: {agent.trigger_keywords}")
```

### Use Progressive Disclosure

```python
from agents.skills import get_skills_registry

# Get skills registry
skills = get_skills_registry()

# List available skills
all_skills = skills.list_skills()
print(f"Total skills: {len(all_skills)}")

# Activate a skill (loads instructions)
await skills.activate_skill("backend-development")

# Load resources when needed
resources = await skills.load_resources("backend-development")

# Check statistics
stats = skills.get_statistics()
print(f"\nSkills Statistics:")
print(f"- Total skills: {stats['total_skills']}")
print(f"- Active skills: {stats['active_skills']}")
print(f"- Context saved: {stats['context_saved']}%")
```

### Use Prompt Library

```python
from agents.prompts.library import get_prompt_library

# Get library
library = get_prompt_library()

# List available templates
workflows = library.list_templates(category='workflow')
print(f"Workflow templates: {len(workflows)}")

# Get a template
prompt = library.get_workflow_template(
    'full-stack-feature',
    variables={
        'task_description': 'Build a user authentication system'
    }
)

print(prompt)
```

## 📊 Monitor Performance

### Check LLM Router Statistics

```python
from agents.routing import get_llm_router

router = get_llm_router()
stats = router.get_statistics()

print("LLM Router Statistics:")
print(f"- Total requests: {stats['total_requests']}")
print(f"- Simple tasks: {stats['simple_tasks']}")
print(f"- Moderate tasks: {stats['moderate_tasks']}")
print(f"- Complex tasks: {stats['complex_tasks']}")
print(f"- Expert tasks: {stats['expert_tasks']}")
print(f"- Cost saved: ${stats['estimated_cost_saved']:.2f}")
if 'cost_savings_percentage' in stats:
    print(f"- Savings: {stats['cost_savings_percentage']}%")
```

### Check Skills Registry Statistics

```python
from agents.skills import get_skills_registry

skills = get_skills_registry()
stats = skills.get_statistics()

print("Skills Registry Statistics:")
print(f"- Total skills: {stats['total_skills']}")
print(f"- Active skills: {stats['active_skills']}")
print(f"- Level 2 loaded: {stats['level_2_loaded']}")
print(f"- Level 3 loaded: {stats['level_3_loaded']}")
print(f"- Context saved: {stats['context_saved']}%")
```

## 🛠️ Development Tips

### 1. Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. Use API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- All endpoints
- Request/response schemas
- Try it out functionality

### 3. Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Automatically reloads on file changes
- **Frontend**: Automatically refreshes on file changes

### 4. Database Inspection

```bash
# Connect to SQLite database
sqlite3 data/autopilot.db

# List tables
.tables

# Query data
SELECT * FROM fractal_agents LIMIT 5;
```

## 📚 Next Steps

1. **Read Documentation**
   - [README_v3.md](README_v3.md) - Full v3.0 documentation
   - [IMPLEMENTATION_V3_SUMMARY.md](IMPLEMENTATION_V3_SUMMARY.md) - Technical details
   - [MIGRATION_TO_V3.md](MIGRATION_TO_V3.md) - Migration guide

2. **Explore Examples**
   - Check `examples/` directory for code samples
   - Review `tests/` for usage patterns

3. **Customize**
   - Add custom agents to Plugin Registry
   - Create custom skills with Progressive Disclosure
   - Build custom workflows with LangGraph

4. **Deploy**
   - See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment
   - Configure environment for production
   - Set up monitoring and logging

## 🆘 Troubleshooting

### Issue: Import Errors

```bash
# Reinstall in development mode
pip install -e .
```

### Issue: Database Not Found

```bash
# Initialize database
python scripts/init_database.py
```

### Issue: Port Already in Use

```bash
# Change port in .env
echo "PORT=8001" >> .env

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: Frontend Won't Start

```bash
# Clear cache and reinstall
cd web-ui
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 💡 Pro Tips

1. **Cost Optimization**: Let LLM Router select models automatically for 77% cost savings
2. **Context Management**: Use Progressive Disclosure for 90% context savings
3. **Agent Discovery**: Browse the agent catalog at http://localhost:3000/agents
4. **Workflow Builder**: Use the visual workflow builder at http://localhost:3000/workflows
5. **Performance**: Monitor the dashboard at http://localhost:3000/dashboard

## 🎉 You're Ready!

You now have AI Assistant Platform v3.0 running with:
- ✅ Enhanced Fractal Agents
- ✅ Plugin Registry with 84 specialized agents
- ✅ Progressive Disclosure Skills System
- ✅ Intelligent LLM Router
- ✅ 57 Prompt Templates
- ✅ Financial Analytics Module
- ✅ LangGraph Workflows

Start building amazing AI-powered applications! 🚀
