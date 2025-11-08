# Database Setup Guide

## Quick Setup

### Step 1: Get Your Supabase Database Password

1. Go to your Supabase dashboard: https://supabase.com/dashboard/project/hbtaablzueprzuwbapyj/settings/database
2. Scroll to "Connection String" section
3. Click "Connection pooling" tab
4. Copy the password shown there
5. Update the DATABASE_URL in `.env` file:

```bash
# Replace [YOUR_DB_PASSWORD] with the actual password
DATABASE_URL=postgresql://postgres.hbtaablzueprzuwbapyj:[YOUR_DB_PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Step 2: Run Migrations

```bash
cd /Users/js/autopilot-core/api/database
python run_migrations.py
```

This will create all 21+ tables:
- ✅ 13 core tables (users, sessions, chat, etc.) - Already exists
- ✅ 5 FractalAgents tables (agents, connectors, memory, skills, routing)
- ✅ 8 Blog Platform tables (categories, authors, posts, comments, etc.)

### Step 3: Verify Setup

```python
python3 << 'EOF'
import asyncio
from agents.postgres_db import get_db

async def verify():
    db = get_db()
    await db.connect()
    tables = await db.get_tables()
    print(f"Total tables: {len(tables)}")
    print("\nFractalAgents tables:")
    for t in sorted([t for t in tables if 'fractal' in t or 'agent' in t]):
        print(f"  ✓ {t}")
    print("\nBlog tables:")
    for t in sorted([t for t in tables if 'blog' in t]):
        print(f"  ✓ {t}")
    await db.disconnect()

asyncio.run(verify())
EOF
```

Expected output: ~21 tables total

---

## Alternative: Local PostgreSQL

If you prefer local development:

```bash
# Start local PostgreSQL
brew services start postgresql@15

# Create database
createdb autopilot

# Update .env
DATABASE_URL=postgresql://autopilot:autopilot@localhost:5432/autopilot

# Run migrations
cd api/database && python run_migrations.py
```

---

## Troubleshooting

### Error: "password authentication failed"
- Double-check you copied the correct password from Supabase
- Make sure you're using the Connection Pooling password, not the Direct Connection password

### Error: "asyncpg not found"
```bash
pip install asyncpg==0.29.0
```

### Error: "relation already exists"
- This is OK if you're re-running migrations
- Tables with IF NOT EXISTS will be skipped

### Check Migration Status
```bash
cd /Users/js/autopilot-core/api/database
ls -la migrations/
# Should see:
# - 001_initial_schema.sql
# - 002_fractal_agents_schema.sql
# - 003_blog_platform_schema.sql
```

---

## Next Steps

After database is set up:

1. **Test Backend API**
   ```bash
   cd /Users/js/autopilot-core
   python -m uvicorn api.server:app --reload --port 8000
   ```

2. **Test Agents**
   ```python
   # Test fractal agent creation
   from agents.fractal import FractalAgentOrchestrator
   # Test blog agent
   from agents.blog import BlogWriterAgent
   ```

3. **Start Frontend**
   ```bash
   cd web-ui
   npm run dev
   ```

---

**Status**: Ready for database password and migration! 🚀
