# 🔧 Рекомендации по настройке Cursor MCP

## 🚨 КРИТИЧНЫЕ ПРОБЛЕМЫ

### ❌ Открытые API ключи в `/Users/js/.cursor/mcp.json`

**НАЙДЕНО:**
- `ANTHROPIC_API_KEY` - ключ Anthropic Claude (начинается с `sk-ant-api03-...`)
- `OPENAI_API_KEY` - ключ OpenAI (начинается с `sk-proj-...`)
- `Magic MCP API_KEY` - API ключ Magic MCP

**РИСКИ:**
- 🔴 Ключи доступны всем приложениям, использующим Cursor
- 🔴 Потенциальная утечка при шаринге конфигурации
- 🔴 Несанкционированное использование ваших API квот

**РЕШЕНИЕ:**
```bash
# 1. Сделайте бэкап (уже сделано)
cp ~/.cursor/mcp.json ~/.cursor/mcp_backup.json

# 2. Замените конфиг на безопасный
cp ~/.cursor/mcp_recommended.json ~/.cursor/mcp.json

# 3. Ротируйте скомпрометированные ключи:
# - Anthropic: https://console.anthropic.com/settings/keys
# - OpenAI: https://platform.openai.com/api-keys
```

---

## ✅ ТЕКУЩАЯ КОНФИГУРАЦИЯ

### Проектный MCP (`/Users/js/autopilot-core/.cursor/mcp.json`)

**Отлично настроено! ✅**

```json
{
  "mcpServers": {
    "ai-assistant-platform": {
      "command": "/Users/js/autopilot-core/venv/bin/python",
      "args": ["/Users/js/autopilot-core/agents/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/js/autopilot-core",
        "DATABASE_PATH": "/Users/js/autopilot-core/data/history.db"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/js/autopilot-core"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@cyanheads/git-mcp-server"],
      "env": {
        "GIT_AUTHOR_NAME": "AI Assistant",
        "GIT_AUTHOR_EMAIL": "ai@autopilot-core.com",
        "GIT_REPO_PATH": "/Users/js/autopilot-core"
      }
    }
  }
}
```

**Доступные инструменты:**
- ✅ 12 инструментов вашей AI платформы (`ai-assistant-platform`)
- ✅ Файловые операции (`filesystem`)
- ✅ Git операции (`git`)

---

## 📋 РЕКОМЕНДАЦИИ ПО ОЧИСТКЕ

### 1. Глобальный MCP (`~/.cursor/mcp.json`)

**Рекомендуемая конфигурация:**

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {},
      "description": "Enhanced reasoning for complex tasks"
    }
  }
}
```

**Что удалить:**
- ❌ `task-master-ai` - содержит открытые ключи + не используется в проекте
- ❌ `filesystem` для `/Users/js/data-parse-desk-2` - неактуальный проект
- ❌ `postgres` - используется Supabase, не локальный Postgres
- ❌ `brave-search` - не используется в проекте
- ❌ `Magic MCP` - содержит открытый ключ
- ❌ `supabase` - дублирует функционал вашего MCP сервера

**Что оставить:**
- ✅ `sequential-thinking` - полезно для сложных задач

### 2. Cursor Rules (`.cursorrules`)

**Текущее состояние: ХОРОШО ✅**

Ваш файл `.cursorrules` уже содержит:
- ✅ Описание проекта и архитектуры
- ✅ Информацию о MCP интеграции
- ✅ Правила безопасности
- ✅ Ссылки на документацию

**Рекомендуемое улучшение:**

```markdown
# AI Assistant Platform - Cursor Rules

Python/FastAPI backend + Next.js 16 frontend + MCP Integration

## Priority Rules (ALWAYS CHECK FIRST)
1. 🔐 SECURITY: NEVER expose API keys, use .env
2. 🔐 VALIDATION: ALWAYS use Pydantic for inputs
3. 🔐 AUTH: JWT required for protected routes
4. 📝 TYPES: Strict TypeScript (NO 'any')
5. 🎨 STYLING: TailwindCSS only (NO inline styles)

## MCP Integration (NEW!)
- **12 MCP Tools Available** via `ai-assistant-platform` server
- Test: `python test_mcp_server.py`
- Config: `.cursor/mcp.json`
- Docs: `MCP_SETUP_GUIDE.md`, `MCP_README.md`

### Available MCP Tools:
1. Projects: `create_project`, `list_projects`
2. Databases: `create_database`, `list_databases`, `query_database`, `create_record`
3. AI Chat: `chat`, `list_chat_sessions`
4. Workflows: `execute_workflow`, `list_workflows`
5. Analytics: `get_stats`, `get_model_rankings`

## Current Features
- 6 AI models with smart routing (Gemini, GPT-4, Claude, DeepSeek, Grok)
- JWT authentication + bcrypt password hashing
- Request caching (920x speedup, MD5-based)
- Rate limiting (3-tier: anonymous, authenticated, premium)
- Streaming chat (SSE)
- Session memory (10 messages context)
- 30+ API endpoints
- MCP Server with 12 tools
- Projects & custom databases with dynamic schemas
- Workflows & integrations
- AI model rankings (7 categories)

## Key Files
- `agents/database.py` - HistoryDatabase class (SQLite ORM)
- `agents/ai_router.py` - Smart model routing + caching
- `agents/auth.py` - JWT authentication
- `agents/mcp_server.py` - **MCP server with 12 tools**
- `agents/rate_limiter.py` - Three-tier rate limiting
- `agents/workflow_engine.py` - Workflow execution
- `api/server.py` - FastAPI application (30+ endpoints)
- `web-ui/app/chat/page.tsx` - Streaming chat UI
- `web-ui/lib/api.ts` - API client

## Development Commands
```bash
# Backend
python api/server.py              # Start FastAPI server (port 8000)

# Frontend
cd web-ui && npm run dev          # Start Next.js dev server (port 3000)

# Testing
python test_mcp_server.py         # Test MCP server (12 tools)
python scripts/smoke_test.py      # Integration tests
python -m pytest tests/           # Unit tests

# Database
python -c "from agents.database import HistoryDatabase; db = HistoryDatabase()"

# MCP
./start_mcp_server.sh             # Start MCP server manually
```

## Security Rules (CRITICAL!)
- ✅ ALWAYS validate inputs with Pydantic models
- ✅ NEVER commit .env files to git
- ✅ JWT required for all protected routes
- ✅ Rate limiting on public endpoints
- ✅ bcrypt for password hashing (12 rounds)
- ✅ CORS properly configured
- ✅ SQL injection prevention via parameterized queries
- ✅ XSS prevention via proper escaping

## Code Style Rules

### Python
```python
# ✅ GOOD
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)

def create_user(data: UserCreate) -> Dict[str, Any]:
    """Create new user with validation."""
    try:
        # Implementation
        return {"success": True, "user_id": 1}
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise

# ❌ BAD
def create_user(email, password):  # No types!
    # No validation, no error handling
    return db.insert(email, password)
```

### TypeScript
```typescript
// ✅ GOOD
interface User {
  id: number;
  email: string;
  createdAt: Date;
}

async function createUser(data: UserCreate): Promise<User> {
  try {
    const response = await api.post('/users', data);
    return response.data;
  } catch (error) {
    console.error('User creation failed:', error);
    throw new Error('Failed to create user');
  }
}

// ❌ BAD
async function createUser(data: any) {  // NO 'any'!
  const response = await api.post('/users', data);
  return response.data;  // No error handling!
}
```

## Documentation
- `README.md` - Main documentation
- `MCP_SETUP_GUIDE.md` - MCP setup (detailed)
- `MCP_README.md` - MCP API reference
- `MCP_БЫСТРЫЙ_СТАРТ.md` - MCP quick start (Russian)
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `CURSOR_MCP_RECOMMENDATIONS.md` - This file

## Architecture
```
┌─────────────────────────────────────┐
│     Cursor IDE with MCP Tools       │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐    ┌────▼──────────┐
│ MCP Server │    │   FastAPI     │
│ 12 tools   │◄───┤   Backend     │
└────────────┘    └────┬──────────┘
                       │
              ┌────────┴────────┐
              │                 │
       ┌──────▼──────┐   ┌─────▼──────┐
       │   SQLite    │   │ AI Models  │
       │   Database  │   │  6 models  │
       └─────────────┘   └────────────┘
```

## When to Use MCP Tools
Use MCP tools in Cursor IDE when you need to:
- 📁 Create/list projects programmatically
- 💾 Query databases with complex filters
- 🤖 Test AI chat routing
- ⚙️ Execute workflows from IDE
- 📊 Get real-time analytics

Example prompts:
```
"List all projects using the MCP tool"
"Create a new database with customer schema"
"Get platform statistics for last 30 days"
"Execute workflow 5 with test data"
```

## Response Format for AI
When generating code:
1. ✅ Read relevant documentation first
2. ✅ Follow security rules (validation, auth, no keys)
3. ✅ Use strict types (Python: type hints, TS: interfaces)
4. ✅ Add error handling (try/except, try/catch)
5. ✅ Add docstrings/comments for complex logic
6. ✅ Test with provided test commands
7. ✅ Explain which patterns you followed

---

**Last Updated:** 2025-11-04
**MCP Integration:** v1.0 (12 tools)
**Project Version:** v1.0.0
```

---

## 🎯 ПЛАН ДЕЙСТВИЙ

### Шаг 1: Безопасность (КРИТИЧНО!)

```bash
# 1. Сделайте бэкап текущего конфига
cp ~/.cursor/mcp.json ~/.cursor/mcp_backup_$(date +%Y%m%d).json

# 2. Замените на безопасную версию
cp ~/.cursor/mcp_recommended.json ~/.cursor/mcp.json

# 3. ВАЖНО: Ротируйте API ключи
# - Anthropic Console: https://console.anthropic.com/settings/keys
# - OpenAI Platform: https://platform.openai.com/api-keys
# - Создайте НОВЫЕ ключи и удалите старые
```

### Шаг 2: Обновите .cursorrules

```bash
# Скопируйте улучшенную версию из этого документа (см. выше)
# в файл /Users/js/autopilot-core/.cursorrules
```

### Шаг 3: Проверка

```bash
cd /Users/js/autopilot-core

# 1. Проверьте MCP сервер
python test_mcp_server.py

# 2. Проверьте проектный MCP конфиг
cat .cursor/mcp.json

# 3. Перезапустите Cursor IDE
```

---

## 📊 СРАВНЕНИЕ КОНФИГУРАЦИЙ

### Было (НЕБЕЗОПАСНО ❌):

```json
{
  "mcpServers": {
    "task-master-ai": {
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-api03-...",  // ❌ ОТКРЫТЫЙ КЛЮЧ!
        "OPENAI_API_KEY": "sk-proj-..."           // ❌ ОТКРЫТЫЙ КЛЮЧ!
      }
    },
    // + 7 других серверов (многие не используются)
  }
}
```

### Стало (БЕЗОПАСНО ✅):

**Глобальный (~/.cursor/mcp.json):**
```json
{
  "mcpServers": {
    "sequential-thinking": {
      // Полезный инструмент, БЕЗ ключей
    }
  }
}
```

**Проектный (/Users/js/autopilot-core/.cursor/mcp.json):**
```json
{
  "mcpServers": {
    "ai-assistant-platform": {
      // Ваш MCP сервер - 12 инструментов
    },
    "filesystem": {
      // Доступ к файлам проекта
    },
    "git": {
      // Git операции
    }
  }
}
```

---

## ✅ ЧЕКЛИСТ

```
[ ] Создан бэкап ~/.cursor/mcp.json
[ ] Заменен ~/.cursor/mcp.json на безопасную версию
[ ] API ключи ротированы (Anthropic, OpenAI)
[ ] Обновлен .cursorrules с MCP информацией
[ ] Протестирован MCP сервер (python test_mcp_server.py)
[ ] Перезапущен Cursor IDE
[ ] Проверена работа MCP инструментов в Cursor
```

---

## 🎓 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

### Почему task-master-ai проблематичен?

1. **Безопасность**: Хранит API ключи в открытом виде
2. **Неактуальность**: Не используется в вашем проекте
3. **Дублирование**: Ваш MCP сервер (`ai-assistant-platform`) более мощный

### Преимущества текущей настройки:

1. ✅ **Безопасность**: Ключи в `.env`, не в MCP конфиге
2. ✅ **Специализация**: MCP сервер заточен под ваш проект
3. ✅ **12 инструментов**: Полный доступ к платформе
4. ✅ **Тестируемость**: `python test_mcp_server.py`
5. ✅ **Документация**: Полные гайды на русском и английском

---

## 📞 ПОДДЕРЖКА

**Документация:**
- MCP Setup: [MCP_SETUP_GUIDE.md](MCP_SETUP_GUIDE.md)
- MCP Reference: [MCP_README.md](MCP_README.md)
- Quick Start (RU): [MCP_БЫСТРЫЙ_СТАРТ.md](MCP_БЫСТРЫЙ_СТАРТ.md)

**Тестирование:**
```bash
python test_mcp_server.py  # Проверка MCP сервера
```

**Файлы конфигурации:**
- Бэкап: `~/.cursor/mcp_backup.json`
- Рекомендуемый: `~/.cursor/mcp_recommended.json`
- Проектный: `/Users/js/autopilot-core/.cursor/mcp.json`

---

**Создано:** 2025-11-04
**Проект:** AI Assistant Platform v1.0
**MCP Version:** 1.20.0
