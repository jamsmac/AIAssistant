# 📋 План доработок AI Assistant Platform

**Дата создания:** 2025-11-04  
**Базовый отчет:** COMPREHENSIVE_ANALYSIS_REPORT.md  
**Статус:** В работе

---

## 🎯 Обзор

Этот план содержит конкретные задачи для улучшения платформы до 100% production readiness. План разбит на фазы с приоритетами и оценками времени.

**Текущая готовность:** 85/100  
**Целевая готовность:** 95/100 (Phase 1-3)

---

## 📊 Приоритеты

- 🔴 **CRITICAL** - Блокеры для production, исправлять немедленно
- 🟠 **HIGH** - Важные улучшения, влияют на UX/performance
- 🟡 **MEDIUM** - Улучшения качества, не блокируют deployment
- 🟢 **LOW** - Nice-to-have, можно отложить

---

## Phase 1: Критические исправления 🔴

**Срок:** 1-2 недели  
**Приоритет:** CRITICAL  
**Цель:** Исправить все блокеры для production deployment

### Task 1.1: Реализовать Cache Methods

**Файл:** `agents/database.py`  
**Проблема:** Методы `get_cached_response()` и `cache_response()` отсутствуют, но вызываются из `ai_router.py`

**Шаги:**

1. Добавить таблицу cache в `_init_db()`:
```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_hash TEXT NOT NULL UNIQUE,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL,
        model TEXT NOT NULL,
        task_type TEXT,
        tokens INTEGER,
        cost REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT NOT NULL,
        use_count INTEGER DEFAULT 0
    )
""")
conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_hash ON cache(prompt_hash)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
```

2. Реализовать `get_cached_response()`:
```python
def get_cached_response(self, prompt: str, task_type: str) -> Optional[Dict]:
    """Получить кэшированный ответ по хешу промпта"""
    import hashlib
    prompt_hash = hashlib.md5(f"{prompt}:{task_type}".encode()).hexdigest()
    
    with sqlite3.connect(self.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM cache
            WHERE prompt_hash = ? AND expires_at > datetime('now')
        """, (prompt_hash,))
        row = cursor.fetchone()
        
        if row:
            # Увеличиваем счетчик использования
            conn.execute("""
                UPDATE cache SET use_count = use_count + 1
                WHERE id = ?
            """, (row['id'],))
            conn.commit()
            
            return {
                'response': row['response'],
                'model': row['model'],
                'created_at': row['created_at'],
                'use_count': row['use_count'] + 1
            }
    return None
```

3. Реализовать `cache_response()`:
```python
def cache_response(self, prompt: str, response: str, model: str, 
                   task_type: str, ttl_hours: int):
    """Сохранить ответ в кэш"""
    import hashlib
    from datetime import datetime, timedelta
    
    prompt_hash = hashlib.md5(f"{prompt}:{task_type}".encode()).hexdigest()
    expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
    
    with sqlite3.connect(self.db_path) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO cache 
            (prompt_hash, prompt, response, model, task_type, expires_at, use_count)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (prompt_hash, prompt[:500], response[:5000], model, task_type, expires_at))
        conn.commit()
```

4. Добавить метод очистки старых кэшей:
```python
def cleanup_expired_cache(self):
    """Удалить истекшие записи кэша"""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute("""
            DELETE FROM cache WHERE expires_at < datetime('now')
        """)
        conn.commit()
        return cursor.rowcount
```

**Тестирование:**
- Проверить кэширование работает
- Проверить TTL правильный
- Проверить cleanup удаляет старые записи

**Оценка времени:** 4-6 часов

---

### Task 1.2: Исправить Database Creation Validation

**Файл:** `api/server.py` (строка ~1405)  
**Проблема:** 422 Unprocessable Entity при создании базы данных

**Шаги:**

1. Проверить формат запроса от фронтенда:
   - Посмотреть что отправляет `web-ui/app/projects/[id]/page.tsx`
   - Убедиться что schema в правильном формате

2. Улучшить валидацию в `DatabaseCreate`:
```python
class DatabaseCreate(BaseModel):
    project_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    schema: Union[DatabaseSchema, List[Dict[str, Any]]] = Field(...)
    
    @validator('schema', pre=True)
    def validate_schema(cls, v):
        if isinstance(v, list):
            # Конвертируем list в DatabaseSchema
            columns = [ColumnDefinition(**col) for col in v]
            return DatabaseSchema(columns=columns)
        return v
```

3. Добавить более детальные error messages:
```python
try:
    # ... validation logic ...
except ValidationError as e:
    raise HTTPException(
        status_code=422,
        detail={
            "error": "Schema validation failed",
            "fields": e.errors(),
            "received": request.schema if hasattr(request, 'schema') else None
        }
    )
```

4. Добавить логирование для debugging:
```python
logger.info(f"Creating database with schema: {type(request.schema)}")
logger.debug(f"Schema content: {request.schema}")
```

**Тестирование:**
- Создать базу данных через API
- Проверить различные форматы schema
- Проверить error messages понятны

**Оценка времени:** 3-4 часа

---

### Task 1.3: Database Migration для user_id

**Файл:** `agents/database.py`  
**Проблема:** Dashboard stats endpoint падает с `no such column: user_id`

**Шаги:**

1. Добавить migration метод:
```python
def migrate_add_user_id_to_requests(self):
    """Добавить user_id column к таблице requests если его нет"""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute("PRAGMA table_info(requests)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logger.info("Adding user_id column to requests table")
            conn.execute("""
                ALTER TABLE requests 
                ADD COLUMN user_id INTEGER
            """)
            conn.commit()
            logger.info("Migration completed: user_id added")
```

2. Вызвать migration в `_init_db()`:
```python
def _init_db(self):
    # ... existing table creation ...
    
    # Run migrations
    self.migrate_add_user_id_to_requests()
```

3. Обновить dashboard stats endpoint для backward compatibility:
```python
# Проверка наличия столбца перед использованием
try:
    cursor = conn.execute("""
        SELECT COUNT(*) FROM requests
        WHERE user_id = ? AND date(timestamp) = date(?)
    """, (user_id, today))
except sqlite3.OperationalError:
    # Fallback для старых БД без user_id
    cursor = conn.execute("""
        SELECT COUNT(*) FROM requests
        WHERE date(timestamp) = date(?)
    """, (today,))
```

**Тестирование:**
- Проверить migration работает на существующих БД
- Проверить dashboard stats endpoint работает
- Проверить backward compatibility

**Оценка времени:** 2-3 часа

---

### Task 1.4: Исправить Integration Tests

**Файлы:** `test_*.py`, `scripts/integration_test.py`  
**Проблема:** 7 тестов не проходят

**Шаги:**

1. **Исправить JWT decode test:**
   - Проверить формат токена
   - Использовать правильную библиотеку для decode
   - Обновить test expectations

2. **Исправить database creation test:**
   - Использовать правильный формат schema
   - Проверить test payload соответствует API

3. **Исправить dashboard stats test:**
   - После migration должно работать
   - Обновить test expectations

4. **Исправить workflow execution test:**
   - Проверить формат ответа от API
   - Обновить test expectations

**Тестирование:**
- Запустить все тесты
- Цель: 85%+ pass rate

**Оценка времени:** 4-6 часов

---

## Phase 2: Улучшения производительности 🟠

**Срок:** 2-3 недели  
**Приоритет:** HIGH  
**Цель:** Оптимизировать производительность на 30-50%

### Task 2.1: Оптимизировать Bundle Size

**Цель:** Уменьшить с 96MB до < 50MB

**Шаги:**

1. Анализ bundle:
```bash
cd web-ui
npm install --save-dev @next/bundle-analyzer
# Добавить в next.config.ts
```

2. Lazy load больших библиотек:
```typescript
// Вместо
import { LineChart } from 'recharts';

// Использовать
const LineChart = dynamic(() => import('recharts').then(m => m.LineChart), {
  ssr: false,
  loading: () => <div>Loading chart...</div>
});
```

3. Оптимизировать imports:
```typescript
// Вместо
import { Icon1, Icon2, Icon3 } from 'lucide-react';

// Использовать tree-shaking friendly imports
import Icon1 from 'lucide-react/dist/esm/icons/icon1';
```

4. Проверить unused dependencies:
```bash
npm run analyze
npx depcheck
```

**Оценка времени:** 6-8 часов

---

### Task 2.2: Добавить Redis для Caching

**Проблема:** Текущий кэш только в SQLite, не масштабируется

**Шаги:**

1. Установить Redis client:
```bash
pip install redis
```

2. Создать Redis cache wrapper:
```python
# agents/redis_cache.py
import redis
import json
from typing import Optional, Dict

class RedisCache:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
    
    def get(self, key: str) -> Optional[Dict]:
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: Dict, ttl: int):
        self.client.setex(key, ttl, json.dumps(value))
```

3. Интегрировать в AI router:
```python
# Fallback: Redis -> SQLite -> None
cached = redis_cache.get(prompt_hash) or db.get_cached_response(...)
```

**Оценка времени:** 4-6 часов

---

### Task 2.3: Оптимизировать Database Queries

**Шаги:**

1. Добавить недостающие индексы:
```sql
CREATE INDEX idx_requests_user_timestamp ON requests(user_id, timestamp);
CREATE INDEX idx_workflows_user_enabled ON workflows(user_id, enabled);
CREATE INDEX idx_database_records_created ON database_records(database_id, created_at);
```

2. Оптимизировать dashboard queries:
```python
# Кэшировать dashboard stats на 5 минут
# Использовать материализованные представления для сложных запросов
```

3. Добавить pagination для всех списков:
```python
# Уже есть limit/offset, но добавить max limit enforcement
limit = min(limit, 100)  # Уже есть в некоторых местах
```

**Оценка времени:** 3-4 часа

---

### Task 2.4: Добавить React Query для Frontend Caching

**Цель:** Кэшировать API запросы на клиенте

**Шаги:**

1. Установить React Query:
```bash
npm install @tanstack/react-query
```

2. Настроить QueryClient:
```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});
```

3. Использовать в компонентах:
```typescript
const { data, isLoading } = useQuery({
  queryKey: ['projects'],
  queryFn: () => api.get('/api/projects'),
});
```

**Оценка времени:** 6-8 часов

---

## Phase 3: Завершение функций 🟡

**Срок:** 3-4 недели  
**Приоритет:** MEDIUM  
**Цель:** Довести функциональность до 95%+

### Task 3.1: Завершить OAuth Integration

**Файлы:** `agents/mcp_client.py`, `api/server.py`  
**Текущий статус:** Placeholder реализация

**Шаги:**

1. Установить Google OAuth библиотеки:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

2. Реализовать полный OAuth flow:
```python
# agents/oauth_manager.py
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

class OAuthManager:
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
            }
        }
    
    def get_authorization_url(self, integration_type: str, user_id: int):
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self._get_scopes(integration_type),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
        )
        
        # Сохранить state для CSRF protection
        state = self._generate_state(user_id, integration_type)
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        return authorization_url, state
    
    def exchange_code_for_tokens(self, code: str, state: str):
        # Verify state
        # Exchange code for tokens
        # Save tokens to database
        pass
```

3. Обновить callback endpoint:
```python
@app.get("/api/integrations/callback")
async def oauth_callback(code: str, state: str):
    # Verify state
    # Exchange code
    # Save tokens
    # Redirect to frontend
    pass
```

**Оценка времени:** 8-10 часов

---

### Task 3.2: Реализовать Schedule Trigger для Workflows

**Файл:** `agents/workflow_engine.py`  
**Текущий статус:** Trigger определен, но не выполняется автоматически

**Шаги:**

1. Установить cron parser:
```bash
pip install croniter
```

2. Создать scheduler service:
```python
# agents/scheduler.py
import croniter
from datetime import datetime
import asyncio

class WorkflowScheduler:
    def __init__(self):
        self.running = False
    
    async def start(self):
        self.running = True
        while self.running:
            await self.check_and_execute()
            await asyncio.sleep(60)  # Check every minute
    
    async def check_and_execute(self):
        # Get all enabled workflows with schedule trigger
        # Check if cron expression matches current time
        # Execute if match
        pass
```

3. Интегрировать в server startup:
```python
# api/server.py
@app.on_event("startup")
async def startup_event():
    scheduler = WorkflowScheduler()
    asyncio.create_task(scheduler.start())
```

**Оценка времени:** 6-8 часов

---

### Task 3.3: Добавить Webhook URL Generation

**Файл:** `api/server.py`  
**Проблема:** Webhook trigger существует, но нет способа получить URL

**Шаги:**

1. Добавить endpoint для получения webhook URL:
```python
@app.get("/api/workflows/{workflow_id}/webhook-url")
async def get_webhook_url(workflow_id: int, token_data: dict = Depends(...)):
    # Generate unique webhook token
    webhook_token = secrets.token_urlsafe(32)
    
    # Save token to workflow
    db.update_workflow_webhook_token(workflow_id, webhook_token)
    
    # Return URL
    base_url = os.getenv("API_URL", "http://localhost:8000")
    return {
        "webhook_url": f"{base_url}/api/webhooks/{webhook_token}",
        "workflow_id": workflow_id
    }
```

2. Добавить webhook endpoint:
```python
@app.post("/api/webhooks/{token}")
async def webhook_handler(token: str, payload: dict):
    # Find workflow by token
    # Execute workflow with payload as context
    pass
```

**Оценка времени:** 4-5 часов

---

### Task 3.4: Реализовать Password Reset Flow

**Файлы:** `api/server.py`, `web-ui/app/auth/reset-password/`  
**Текущий статус:** Не реализовано

**Шаги:**

1. Добавить таблицу password_reset_tokens:
```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
```

2. Добавить endpoints:
```python
@app.post("/api/auth/forgot-password")
async def forgot_password(email: EmailStr):
    # Generate token
    # Send email (или логировать для MVP)
    # Return success

@app.post("/api/auth/reset-password")
async def reset_password(token: str, new_password: str):
    # Verify token
    # Update password
    # Mark token as used
    pass
```

3. Создать frontend страницы:
- `/auth/forgot-password`
- `/auth/reset-password/[token]`

**Оценка времени:** 6-8 часов

---

### Task 3.5: Добавить Refresh Token Mechanism

**Файл:** `agents/auth.py`  
**Текущий статус:** Только access token

**Шаги:**

1. Добавить таблицу refresh_tokens:
```python
conn.execute("""
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL UNIQUE,
        expires_at TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
```

2. Модифицировать login/register:
```python
def create_tokens(user_id: int, email: str):
    access_token = create_jwt_token(user_id, email, expires_hours=1)
    refresh_token = create_refresh_token(user_id)
    
    # Save refresh token to DB
    db.save_refresh_token(user_id, refresh_token)
    
    return access_token, refresh_token
```

3. Добавить refresh endpoint:
```python
@app.post("/api/auth/refresh")
async def refresh_token(refresh_token: str):
    # Verify refresh token
    # Generate new access token
    # Return new tokens
    pass
```

**Оценка времени:** 4-5 часов

---

## Phase 4: Production Hardening 🟠

**Срок:** 2-3 недели  
**Приоритет:** HIGH  
**Цель:** Улучшить надежность и мониторинг

### Task 4.1: Улучшить Error Handling и Logging

**Шаги:**

1. Создать custom exception classes:
```python
# agents/exceptions.py
class APIError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(APIError):
    def __init__(self, message: str, fields: dict = None):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR")
        self.fields = fields
```

2. Добавить request ID для tracing:
```python
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

3. Улучшить логирование:
```python
import structlog

logger = structlog.get_logger()
logger.info("request_completed", 
           request_id=request.state.request_id,
           endpoint=request.url.path,
           status_code=response.status_code,
           duration_ms=duration)
```

**Оценка времени:** 6-8 часов

---

### Task 4.2: Добавить Monitoring и Alerting

**Шаги:**

1. Интегрировать Sentry (уже настроено):
   - Проверить что работает
   - Настроить alerts для критических ошибок

2. Добавить health check improvements:
```python
@app.get("/api/health/detailed")
async def detailed_health():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "ai_models": await check_ai_models(),
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

3. Добавить metrics endpoint:
```python
@app.get("/api/metrics")
async def metrics():
    return {
        "requests_total": get_request_count(),
        "requests_per_second": get_rps(),
        "error_rate": get_error_rate(),
        "average_response_time": get_avg_response_time(),
    }
```

**Оценка времени:** 4-6 часов

---

### Task 4.3: Настроить Backup Strategy

**Шаги:**

1. Создать backup script:
```python
# scripts/backup_database.py
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/history_{timestamp}.db"
    
    shutil.copy2("data/history.db", backup_path)
    
    # Upload to S3 or backup storage
    # Keep only last N backups
```

2. Настроить автоматический backup:
```bash
# Добавить в cron
0 2 * * * /path/to/backup_database.py
```

3. Добавить restore functionality:
```python
def restore_database(backup_path: str):
    # Verify backup
    # Restore database
    # Verify integrity
    pass
```

**Оценка времени:** 3-4 часа

---

### Task 4.4: Улучшить Rate Limiting

**Текущий статус:** Работает, но можно улучшить

**Шаги:**

1. Добавить Redis для distributed rate limiting:
```python
# Если используется несколько инстансов
def check_rate_limit_redis(identifier: str, tier: str):
    key = f"ratelimit:{tier}:{identifier}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)
    return current <= limits[tier]
```

2. Добавить более детальные headers:
```python
response.headers["X-RateLimit-Limit"] = str(limit)
response.headers["X-RateLimit-Remaining"] = str(remaining)
response.headers["X-RateLimit-Reset"] = str(reset_time)
```

3. Добавить rate limit для разных endpoints:
```python
# Разные лимиты для разных endpoints
rate_limits = {
    "/api/chat": (10, 60),
    "/api/projects": (50, 60),
    "/api/workflows": (20, 60),
}
```

**Оценка времени:** 4-5 часов

---

## Phase 5: Code Quality Improvements 🟡

**Срок:** 2-3 недели  
**Приоритет:** MEDIUM

### Task 5.1: Разделить api/server.py на модули

**Проблема:** 3000+ строк в одном файле

**Шаги:**

1. Создать структуру роутеров:
```
api/
├── server.py (main app)
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── projects.py
│   ├── workflows.py
│   ├── integrations.py
│   ├── dashboard.py
│   ├── chat.py
│   └── rankings.py
├── dependencies.py (auth, rate_limit)
└── exceptions.py (custom exceptions)
```

2. Пример структуры router:
```python
# api/routers/projects.py
from fastapi import APIRouter, Depends
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.post("", response_model=ProjectDetail)
async def create_project(...):
    pass

@router.get("", response_model=List[ProjectDetail])
async def list_projects(...):
    pass
```

3. Обновить server.py:
```python
from routers import auth, projects, workflows, ...

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(workflows.router)
```

**Оценка времени:** 8-10 часов

---

### Task 5.2: Добавить Database Abstraction Layer

**Цель:** Упростить переход на PostgreSQL

**Шаги:**

1. Создать базовый класс:
```python
# agents/db_base.py
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    @abstractmethod
    def execute_query(self, query: str, params: tuple):
        pass
    
    @abstractmethod
    def execute_transaction(self, queries: list):
        pass
```

2. Реализовать для SQLite:
```python
class SQLiteAdapter(DatabaseAdapter):
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute_query(self, query: str, params: tuple):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(query, params)
```

3. Использовать adapter вместо прямых вызовов:
```python
# Вместо прямого sqlite3.connect
db = DatabaseAdapter()
results = db.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
```

**Оценка времени:** 6-8 часов

---

### Task 5.3: Добавить React Query для State Management

**Уже упомянуто в Phase 2, Task 2.4**

---

## Phase 6: Future Enhancements 🟢

**Срок:** 4-6 недель  
**Приоритет:** LOW

### Task 6.1: Переход на PostgreSQL

**Цель:** Масштабируемость для production

**Шаги:**

1. Подготовить migration scripts
2. Протестировать на staging
3. Миграция данных
4. Обновить connection strings

**Оценка времени:** 2-3 дня

---

### Task 6.2: Добавить Read Replicas

**Цель:** Улучшить производительность чтения

**Оценка времени:** 2-3 дня

---

### Task 6.3: Implement 2FA

**Цель:** Улучшить безопасность

**Оценка времени:** 1-2 дня

---

## 📅 Временная шкала

### Неделя 1-2: Phase 1 (Critical Fixes)
- ✅ Task 1.1: Cache methods (4-6h)
- ✅ Task 1.2: Database validation (3-4h)
- ✅ Task 1.3: Migration (2-3h)
- ✅ Task 1.4: Fix tests (4-6h)
- **Итого:** ~15-20 часов

### Неделя 3-4: Phase 2 (Performance)
- ✅ Task 2.1: Bundle optimization (6-8h)
- ✅ Task 2.2: Redis caching (4-6h)
- ✅ Task 2.3: Query optimization (3-4h)
- ✅ Task 2.4: React Query (6-8h)
- **Итого:** ~20-26 часов

### Неделя 5-7: Phase 3 (Feature Completion)
- ✅ Task 3.1: OAuth (8-10h)
- ✅ Task 3.2: Schedule trigger (6-8h)
- ✅ Task 3.3: Webhook URLs (4-5h)
- ✅ Task 3.4: Password reset (6-8h)
- ✅ Task 3.5: Refresh tokens (4-5h)
- **Итого:** ~28-36 часов

### Неделя 8-9: Phase 4 (Hardening)
- ✅ Task 4.1: Error handling (6-8h)
- ✅ Task 4.2: Monitoring (4-6h)
- ✅ Task 4.3: Backups (3-4h)
- ✅ Task 4.4: Rate limiting (4-5h)
- **Итого:** ~17-23 часа

### Неделя 10-11: Phase 5 (Code Quality)
- ✅ Task 5.1: Split server.py (8-10h)
- ✅ Task 5.2: DB abstraction (6-8h)
- **Итого:** ~14-18 часов

**Общая оценка времени:** 94-123 часа (~12-15 рабочих дней)

---

## 🎯 Success Metrics

После завершения всех фаз:

| Метрика | Текущее | Цель | Статус |
|---------|---------|------|--------|
| Test Pass Rate | 70.8% | > 85% | ⏳ |
| Bundle Size | 96MB | < 50MB | ⏳ |
| API Response Time | ~200ms | < 150ms | ⏳ |
| Cache Hit Rate | 0% | > 80% | ⏳ |
| Feature Completeness | 85% | > 95% | ⏳ |
| Code Quality Score | 85/100 | > 95/100 | ⏳ |

---

## 📝 Приоритизация задач

### Must Have (для production):
1. ✅ Phase 1: Все критические исправления
2. ✅ Phase 4: Production hardening (частично)

### Should Have (для улучшения):
3. ✅ Phase 2: Performance optimization
4. ✅ Phase 3: Feature completion (OAuth, schedule)

### Nice to Have (для future):
5. ⏳ Phase 5: Code quality improvements
6. ⏳ Phase 6: Future enhancements

---

## 🚀 Quick Wins (можно сделать сразу)

1. **Реализовать cache methods** (4-6 часов) - сразу улучшит производительность
2. **Исправить database validation** (3-4 часа) - разблокирует создание БД
3. **Добавить migration** (2-3 часа) - исправит dashboard stats
4. **Оптимизировать bundle** (6-8 часов) - улучшит загрузку фронтенда

**Итого:** ~15-20 часов работы для значительного улучшения

---

## 📌 Следующие шаги

1. **Сегодня:** Начать с Task 1.1 (Cache methods) - самый быстрый impact
2. **На этой неделе:** Завершить Phase 1 (все критические исправления)
3. **На следующей неделе:** Начать Phase 2 (Performance)
4. **Через 2 недели:** Review прогресса и приоритизировать Phase 3-4

---

**План создан:** 2025-11-04  
**Последнее обновление:** 2025-11-04  
**Статус:** Ready for execution





