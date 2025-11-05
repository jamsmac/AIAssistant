# 🚀 AI Assistant Platform v4.5 - FractalAgents & Blog Platform

**Complete AI-Powered Platform with Self-Organizing Agents**

---

## 🎯 What's New in v4.5

### ✨ Major Features

1. **FractalAgents System** - Self-organizing AI agent network
   - Dynamic task routing based on agent skills
   - Collective memory and learning
   - Hierarchical task decomposition
   - Agent-to-agent collaboration

2. **AI-Powered Blog Platform**
   - Automated content creation with AI
   - SEO optimization
   - Social media post generation
   - Image prompt generation
   - Complete CMS functionality

3. **PostgreSQL Integration**
   - Production-ready database
   - Advanced indexing and optimization
   - Triggers and views for automation
   - 14 tables with full relationships

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Node.js 18+ (for frontend)
- Anthropic API key

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for web-ui)
cd web-ui
npm install
cd ..
```

### 2. Configure Environment

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/aiassistant

# AI APIs
ANTHROPIC_API_KEY=sk-ant-...

# Optional
STABILITY_API_KEY=sk-...  # For image generation
OPENAI_API_KEY=sk-...     # Optional alternative
```

### 3. Initialize Database

```bash
# Run migration (creates all tables)
python scripts/migrate_to_postgres.py

# Initialize agents (creates default agent network)
python scripts/init_agents.py
```

This will create:
- Root orchestrator agent
- 5 Blog-specific agents (Writer, Editor, SEO, Image, Social)
- 2 General agents (Analyst, Code Assistant)
- Connectors between agents

### 4. Start Services

```bash
# Start API server
python -m uvicorn api.server:app --reload --port 8000

# In another terminal, start frontend
cd web-ui
npm run dev
```

Access:
- API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## 🎨 Architecture Overview

```
┌─────────────────────────────────────────────┐
│           USER INTERFACE (Next.js)          │
│  Blog │ Admin │ Chat │ Agents Dashboard     │
└────────────────┬────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────┐
│         FASTAPI BACKEND                     │
│  ┌──────────┐  ┌────────────────────────┐  │
│  │ Blog API │  │  FractalAgents API     │  │
│  └──────────┘  └────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  FRACTAL AGENT ORCHESTRATOR          │  │
│  │                                      │  │
│  │  [Root] ─┬─> [Writer] ──> [Editor]  │  │
│  │          ├─> [SEO]    ──> [Image]   │  │
│  │          ├─> [Social] ──> [...]     │  │
│  │          └─> [Analyst] ─> [Coder]   │  │
│  │                                      │  │
│  │  [Collective Memory] [Connectors]   │  │
│  └──────────────────────────────────────┘  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│      POSTGRESQL DATABASE                    │
│  • FractalAgents (6 tables)                 │
│  • Blog Platform (8 tables)                 │
│  • Analytics & Metrics                      │
└─────────────────────────────────────────────┘
```

---

## 🤖 FractalAgents API

### Process Task

```bash
POST /api/fractal/task
```

```json
{
  "description": "Analyze this dataset and create a report",
  "required_skills": ["data_analysis", "reporting"],
  "type": "analysis"
}
```

**Response:**

```json
{
  "task_id": "uuid",
  "agent_id": "analyst-agent-id",
  "agent_name": "DataAnalyst",
  "response": "Detailed analysis and report...",
  "success": true,
  "execution_time": 2500,
  "tokens_used": 1500
}
```

### List Agents

```bash
GET /api/fractal/agents
```

### Create Agent

```bash
POST /api/fractal/agents
```

```json
{
  "name": "CustomAgent",
  "skills": ["skill1", "skill2"],
  "agent_type": "specialist",
  "description": "Custom agent for specific tasks"
}
```

### System Status

```bash
GET /api/fractal/system-status
```

**Response:**

```json
{
  "organization_id": "default",
  "agents": {
    "total": 8,
    "by_type": [
      {"type": "root", "count": 1, "avg_success_rate": 1.0},
      {"type": "specialist", "count": 7, "avg_success_rate": 0.95}
    ]
  },
  "connectors": {"total": 15},
  "collective_memory": {
    "total_entries": 150,
    "success_rate": 0.92,
    "avg_confidence": 0.85
  },
  "status": "healthy"
}
```

---

## 📝 Blog Platform API

### Generate Blog Post with AI

```bash
POST /api/blog/ai/generate
```

```json
{
  "topic": "Introduction to FractalAgents",
  "category": "tutorial",
  "style": "professional",
  "target_length": 1500,
  "auto_seo": true,
  "generate_image": true
}
```

**Response:**

```json
{
  "title": "Understanding FractalAgents: A Complete Guide",
  "excerpt": "Learn how self-organizing AI agents...",
  "content": "Full markdown content...",
  "suggested_tags": ["ai", "agents", "automation"],
  "reading_time": 8,
  "seo": {
    "optimized_title": "...",
    "meta_description": "...",
    "seo_score": 85
  },
  "image": {
    "image_prompt": "...",
    "alt_text": "..."
  }
}
```

### Create Blog Post

```bash
POST /api/blog/posts
```

```json
{
  "title": "My Blog Post",
  "content": "Content in Markdown...",
  "category_id": "uuid",
  "tags": ["tag1", "tag2"],
  "use_ai": false,
  "ai_improve": true,
  "auto_seo": true
}
```

### Publish Post

```bash
PUT /api/blog/posts/{post_id}/publish?publish_to_social=true
```

Auto-generates social media posts for Twitter, LinkedIn, etc.

### List Posts

```bash
GET /api/blog/posts?category=tutorial&page=1&per_page=10
```

### Get Post Analytics

```bash
GET /api/blog/posts/{post_id}/analytics
```

---

## 💡 Usage Examples

### Example 1: AI-Powered Blog Post Creation

```python
import requests

# Generate complete blog post with AI
response = requests.post('http://localhost:8000/api/blog/ai/generate', json={
    'topic': 'How to build scalable microservices',
    'category': 'technical',
    'style': 'professional',
    'target_length': 2000,
    'auto_seo': True
})

post_data = response.json()

# Create post in database
post_response = requests.post('http://localhost:8000/api/blog/posts', json={
    'title': post_data['title'],
    'content': post_data['content'],
    'excerpt': post_data['excerpt'],
    'tags': post_data['suggested_tags']
})

post_id = post_response.json()['post_id']

# Publish with social media
requests.put(f'http://localhost:8000/api/blog/posts/{post_id}/publish',
             params={'publish_to_social': True})

print(f"✓ Blog post published: {post_data['title']}")
```

### Example 2: Custom Agent Task Processing

```python
# Process complex task through agent network
task_response = requests.post('http://localhost:8000/api/fractal/task', json={
    'description': 'Analyze user engagement data from last month and suggest improvements',
    'required_skills': ['data_analysis', 'insights', 'reporting'],
    'type': 'analysis'
})

result = task_response.json()

print(f"Task processed by: {result['agent_name']}")
print(f"Result: {result['response']}")
print(f"Execution time: {result['execution_time']}ms")
```

### Example 3: Multi-Agent Collaboration

When you submit a complex task, multiple agents collaborate automatically:

```python
# Complex task requiring multiple skills
task_response = requests.post('http://localhost:8000/api/fractal/task', json={
    'description': '''Create a comprehensive blog post about AI agents,
                      optimize it for SEO, generate a cover image,
                      and create social media posts''',
    'required_skills': ['blog_writing', 'seo_optimization', 'image_generation', 'social_media'],
    'type': 'content_creation'
})

# The root agent will:
# 1. Route to Writer agent → creates blog post
# 2. Route to SEO agent → optimizes for search
# 3. Route to Image agent → generates image prompt
# 4. Route to Social agent → creates social posts
# 5. Aggregate all results

result = task_response.json()
print(result['sub_results'])  # See each agent's contribution
```

---

## 📊 Database Schema

### FractalAgents Tables (6 tables)

1. **fractal_agents** - Agent definitions
2. **agent_connectors** - Connections between agents
3. **agent_collective_memory** - Shared learning and memory
4. **agent_skills** - Skills registry
5. **task_routing_history** - Routing decisions log
6. **agent_performance_metrics** - Time-series metrics

### Blog Platform Tables (8 tables)

1. **blog_categories** - Post categories
2. **blog_authors** - Author profiles
3. **blog_posts** - Blog posts (main table)
4. **blog_post_versions** - Version history
5. **blog_comments** - Comment system
6. **blog_subscriptions** - Newsletter subscribers
7. **blog_social_shares** - Share tracking
8. **blog_analytics** - Detailed analytics

---

## 🔧 Configuration

### Agent Configuration

Edit agent properties:

```bash
PUT /api/fractal/agents/{agent_id}
```

```json
{
  "trust_level": 0.9,
  "temperature": 0.7,
  "max_tokens": 4096,
  "system_prompt": "Custom prompt..."
}
```

### Connector Configuration

Create custom agent connections:

```bash
POST /api/fractal/connectors
```

```json
{
  "from_agent_id": "agent1-id",
  "to_agent_id": "agent2-id",
  "connector_type": "peer",
  "strength": 0.8,
  "trust": 0.9
}
```

---

## 📈 Monitoring & Analytics

### System Health

```bash
GET /api/fractal/system-status
```

Returns:
- Agent count and types
- Success rates
- Memory statistics
- Recent activity
- Overall health status

### Agent Performance

```bash
GET /api/fractal/agents/{agent_id}
```

Returns:
- Task completion stats
- Success rate
- Average response time
- Recent task history
- Connections

### Blog Analytics

```bash
GET /api/blog/analytics/overview
```

Returns:
- Total posts, views, likes
- Popular posts
- Traffic sources
- Device breakdown

---

## 🚀 Deployment

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: aiassistant
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/aiassistant
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres

  frontend:
    build: ./web-ui
    environment:
      NEXT_PUBLIC_API_URL: http://api:8000
```

Run:

```bash
docker-compose up -d
```

### Production Checklist

- [ ] Set strong database password
- [ ] Configure CORS origins
- [ ] Enable rate limiting
- [ ] Set up SSL/TLS
- [ ] Configure backup strategy
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up error tracking (Sentry)

---

## 📚 API Documentation

Full interactive API documentation available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Testing

Run tests:

```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/test_integration.py

# API tests
pytest tests/test_api.py
```

---

## 🤝 Contributing

See [FRACTAL_AGENTS_IMPLEMENTATION_PLAN.md](FRACTAL_AGENTS_IMPLEMENTATION_PLAN.md) for architecture details and development roadmap.

---

## 📄 License

[Your License Here]

---

## 🎓 Learn More

- **Architecture**: See [FRACTAL_AGENTS_IMPLEMENTATION_PLAN.md](FRACTAL_AGENTS_IMPLEMENTATION_PLAN.md)
- **API Reference**: http://localhost:8000/docs
- **Database Schema**: See `scripts/init_fractal_schema.sql` and `scripts/init_blog_schema.sql`

---

**Built with:**
- FastAPI
- PostgreSQL
- Anthropic Claude
- Next.js
- React

**Version:** 4.5 Ultimate - FractalAgents Edition
