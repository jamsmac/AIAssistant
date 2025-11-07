"""
FastAPI сервер для AI Development System
Предоставляет REST API для взаимодействия с AI агентами
"""
import sys
import os
import logging
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import uvicorn
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
import csv
import io
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("RELEASE_VERSION", "1.0.0")
    )

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))
# Добавляем путь к директории agents
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from ai_router import AIRouter
from database import get_db
from ranking_collector import RankingCollector
from auth import hash_password, verify_password, create_jwt_token, verify_jwt_token as verify_jwt
from rate_limiter import get_rate_limiter
from csrf_protection import get_csrf_protection
from oauth_providers import oauth_manager
from two_factor_auth import TwoFactorAuth
from monitoring import metrics_collector, alert_manager, request_monitor, system_monitor, AlertSeverity

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="AI Development System API",
    description="REST API для управления AI агентами и автоматизации разработки",
    version="1.0.0"
)

# CORS для веб-интерфейса
# В production домены читаются из переменной окружения CORS_ORIGINS
# Формат: CORS_ORIGINS=https://app.example.com,https://www.example.com
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",  # Vite dev server
]

# Получаем production домены из env переменной
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
if CORS_ORIGINS_ENV:
    # Разделяем по запятой и очищаем пробелы
    production_origins = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()]
    ALLOWED_ORIGINS = DEFAULT_ORIGINS + production_origins
else:
    ALLOWED_ORIGINS = DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Gzip compression middleware для улучшения производительности
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Сжимаем ответы > 1KB

# CSP Headers Middleware для защиты от XSS
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' http://localhost:* ws://localhost:* https://api.openai.com https://api.anthropic.com; "
            "frame-ancestors 'none'; "
            "form-action 'self';"
        )

        # Дополнительные security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS для production (раскомментировать при HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

app.add_middleware(SecurityHeadersMiddleware)

# API Version Middleware - добавляет версию API в заголовки ответов
class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления версии API в заголовки ответов"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = app.version
        response.headers["X-API-Server"] = "AI Assistant Platform"
        return response

app.add_middleware(APIVersionMiddleware)

# ============================================
# Monitoring Middleware
# ============================================

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware для мониторинга запросов и производительности"""

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            request_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration:.3f}"

            # Alert on slow requests
            if duration > 10:  # More than 10 seconds
                alert_manager.create_alert(
                    severity=AlertSeverity.WARNING,
                    title="Slow Request Detected",
                    message=f"Request to {request.url.path} took {duration:.2f} seconds",
                    source="MonitoringMiddleware",
                    metadata={
                        "method": request.method,
                        "path": request.url.path,
                        "duration": duration
                    }
                )

            return response

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            request_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration
            )

            # Report to Sentry
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)

            # Create alert for critical errors
            alert_manager.create_alert(
                severity=AlertSeverity.ERROR,
                title="Request Failed",
                message=str(e),
                source="MonitoringMiddleware",
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                }
            )

            raise

app.add_middleware(MonitoringMiddleware)

# Инициализация AI Router
router = AIRouter()

# ============================================
# Include Routers
# ============================================

# Import and include chat router
try:
    from api.routers import chat_router
    app.include_router(chat_router.router)
    logger.info("Chat router loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load chat router: {e}")

# Import and include credit router
try:
    from api.routers import credit_router
    app.include_router(credit_router.router)
    logger.info("Credit router loaded successfully")
except ImportError as e:
    logger.warning(f"Could not load credit router: {e}")

# ============================================
# Startup and Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting AI Development System API")

    # Start workflow scheduler for scheduled triggers
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "agents"))
        from workflow_scheduler import start_scheduler
        start_scheduler()
        logger.info("Workflow scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start workflow scheduler: {e}")

    # Start system monitoring
    asyncio.create_task(system_monitor.start(interval=60))

    # Initialize alert channels if configured
    if os.getenv("SMTP_HOST"):
        from monitoring import EmailNotificationChannel
        email_channel = EmailNotificationChannel(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", 587)),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            to_emails=os.getenv("ALERT_EMAILS", "").split(",")
        )
        alert_manager.add_notification_channel(email_channel)

    if os.getenv("WEBHOOK_URL"):
        from monitoring import WebhookNotificationChannel
        webhook_channel = WebhookNotificationChannel(os.getenv("WEBHOOK_URL"))
        alert_manager.add_notification_channel(webhook_channel)

    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Development System API")

    # Stop workflow scheduler
    try:
        from workflow_scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Workflow scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping workflow scheduler: {e}")

    system_monitor.stop()

# ============================================
# Pydantic Models (схемы данных)
# ============================================

class ChatRequest(BaseModel):
    """Запрос к AI модели"""
    prompt: str = Field(..., description="Текст запроса", min_length=1)
    task_type: Literal['architecture', 'code', 'review', 'test', 'devops', 'research', 'chat', 'general'] = Field(
        default='chat',
        description="Тип задачи"
    )
    complexity: int = Field(default=5, ge=1, le=10, description="Сложность задачи (1-10)")
    budget: Literal['free', 'cheap', 'medium', 'expensive'] = Field(
        default='cheap',
        description="Бюджетный лимит"
    )
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Ответ от AI"""
    response: str
    model: str
    tokens: int
    cost: float
    error: bool = False

class ProjectRequest(BaseModel):
    """Запрос на создание проекта"""
    idea: str = Field(..., description="Описание идеи проекта", min_length=10)
    budget: Literal['free', 'cheap', 'medium', 'premium'] = Field(
        default='medium',
        description="Бюджетный лимит"
    )

class ProjectResponse(BaseModel):
    """Ответ с результатом создания проекта"""
    project_id: str
    architecture: dict
    code: dict
    review: dict
    total_cost: float
    status: str

class StatsResponse(BaseModel):
    """Статистика использования"""
    calls: int
    tokens: int
    cost: float
    avg_cost_per_call: float
    by_model: dict
    available_models: dict

class HealthResponse(BaseModel):
    """Статус здоровья сервиса"""
    status: str
    services: dict
    router_stats: dict

class HistoryResponse(BaseModel):
    """Ответ с историей запросов"""
    total: int
    items: list
    page: int
    limit: int

class HistoryStatsResponse(BaseModel):
    """Статистика по истории"""
    general: dict
    by_model: list
    by_task: list
    by_date: list

# ============================================
# Authentication Models
# ============================================

class RegisterRequest(BaseModel):
    """Запрос на регистрацию нового пользователя"""
    email: EmailStr
    password: str = Field(min_length=8, description="Password (min 8 characters)")

class LoginRequest(BaseModel):
    """Запрос на вход в систему"""
    email: EmailStr
    password: str

class UserInfo(BaseModel):
    """Информация о пользователе"""
    id: int
    email: str
    created_at: str
    last_login_at: Optional[str] = None

class AuthResponse(BaseModel):
    """Ответ с токеном аутентификации"""
    token: str
    user: UserInfo

# ============================================
# Projects Management Models
# ============================================

class ProjectCreate(BaseModel):
    """Запрос на создание проекта"""
    name: str = Field(..., min_length=1, max_length=100, description="Название проекта")
    description: Optional[str] = Field(None, max_length=500, description="Описание проекта")

class ProjectUpdate(BaseModel):
    """Запрос на обновление проекта"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Новое название")
    description: Optional[str] = Field(None, max_length=500, description="Новое описание")

class ProjectDetail(BaseModel):
    """Информация о проекте"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: str
    database_count: int = 0

# ============================================
# Databases Management Models
# ============================================

class ColumnDefinition(BaseModel):
    """Определение колонки в схеме"""
    name: str = Field(..., min_length=1, max_length=50, description="Название колонки")
    type: Literal['text', 'number', 'boolean', 'date', 'select'] = Field(..., description="Тип данных")
    required: bool = Field(default=False, description="Обязательное поле")
    options: Optional[List[str]] = Field(None, description="Опции для select type")
    min_length: Optional[int] = Field(None, description="Минимальная длина для text")
    max_length: Optional[int] = Field(None, description="Максимальная длина для text")
    min_value: Optional[float] = Field(None, description="Минимальное значение для number")
    max_value: Optional[float] = Field(None, description="Максимальное значение для number")

class DatabaseSchema(BaseModel):
    """Схема базы данных"""
    columns: List[ColumnDefinition] = Field(..., description="Список колонок", min_length=1)

class DatabaseCreate(BaseModel):
    """Запрос на создание базы данных"""
    project_id: int = Field(..., gt=0, description="ID проекта")
    name: str = Field(..., min_length=1, max_length=100, description="Название базы данных")
    description: Optional[str] = Field(None, description="Описание базы данных")
    schema: Union[DatabaseSchema, List[Dict[str, Any]]] = Field(..., description="Схема базы данных")

    class Config:
        protected_namespaces = ()

class DatabaseResponse(BaseModel):
    """Ответ с информацией о базе данных"""
    id: int
    project_id: int
    name: str
    schema: DatabaseSchema
    record_count: int = 0
    created_at: str

    class Config:
        protected_namespaces = ()

class RecordCreate(BaseModel):
    """Запрос на создание записи"""
    database_id: Optional[int] = Field(None, description="ID базы данных (для /api/records endpoint)")
    data: Dict[str, Any] = Field(..., description="Данные записи")

class RecordUpdate(BaseModel):
    """Запрос на обновление записи"""
    data: Dict[str, Any] = Field(..., description="Новые данные записи")

class RecordResponse(BaseModel):
    """Ответ с информацией о записи"""
    id: int
    database_id: int
    data: Dict[str, Any]
    created_at: str
    updated_at: str


# ============================================
# Workflow Models
# ============================================

class WorkflowTrigger(BaseModel):
    """Триггер workflow"""
    type: Literal['manual', 'schedule', 'webhook', 'email_received', 'record_created']
    config: Dict[str, Any] = {}


class WorkflowAction(BaseModel):
    """Действие workflow"""
    type: str  # send_email, create_record, call_webhook, etc.
    config: Dict[str, Any]


class WorkflowCreate(BaseModel):
    """Запрос на создание workflow"""
    name: str = Field(..., min_length=1, max_length=100)
    trigger: WorkflowTrigger
    actions: List[WorkflowAction] = Field(..., min_items=1)
    enabled: bool = True


class WorkflowUpdate(BaseModel):
    """Запрос на обновление workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    trigger: Optional[WorkflowTrigger] = None
    actions: Optional[List[WorkflowAction]] = Field(None, min_items=1)
    enabled: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """Ответ с информацией о workflow"""
    id: int
    user_id: int
    name: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    enabled: bool
    created_at: str


class ExecutionResponse(BaseModel):
    """Ответ с информацией о выполнении workflow"""
    id: int
    workflow_id: int
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    executed_at: str


# === INTEGRATIONS MODELS ===

class IntegrationInfo(BaseModel):
    """Information about an integration"""
    type: Literal['gmail', 'google_drive', 'telegram']
    name: str
    description: str
    icon: str
    requires_oauth: bool
    status: Literal['connected', 'disconnected', 'error']
    last_sync: Optional[str] = None


class ConnectRequest(BaseModel):
    """Request to connect an integration"""
    integration_type: str
    # For Telegram (bot token and chat_id)
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "status": "running",
        "message": "AI Development System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Отправить запрос к AI
    
    Примеры:
```json
    {
        "prompt": "Напиши функцию для сортировки массива",
        "task_type": "code",
        "complexity": 3,
        "budget": "free"
    }
```
    """
    try:
        result = router.route(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            session_id=request.session_id
        )
        
        # Сохраняем в историю
        db = get_db()
        db.add_request(
            prompt=request.prompt,
            response=result['response'],
            model=result['model'],
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            tokens=result.get('tokens', 0),
            cost=result.get('cost', 0.0),
            error=result.get('error', False)
        )
        
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """
    Создать полный проект из идеи
    
    Выполняет полный цикл:
    1. Создание архитектуры (Claude/GPT-4)
    2. Генерация кода (GPT-4/DeepSeek)
    3. Код-ревью (Gemini/DeepSeek)
    
    Примеры:
```json
    {
        "idea": "CRM система для управления вендинговыми автоматами",
        "budget": "medium"
    }
```
    """
    try:
        # 1. Архитектура
        print(f"📐 Creating architecture for: {request.idea}")
        architecture = router.route(
            prompt=f"""Create detailed software architecture for this project:

Project: {request.idea}

Include:
1. Tech stack recommendations
2. System architecture (frontend, backend, database)
3. API endpoints structure
4. Database schema
5. Key components and their responsibilities

Return in structured format.""",
            task_type='architecture',
            complexity=8,
            budget=request.budget
        )
        
        # 2. Генерация кода
        print(f"💻 Generating code...")
        code = router.route(
            prompt=f"""Based on this architecture, generate production-ready starter code:

ARCHITECTURE:
{architecture['response']}

Generate:
1. Main application structure
2. Core API endpoints (at least 3)
3. Database models
4. Configuration files

Use TypeScript for frontend, Python/FastAPI for backend.""",
            task_type='code',
            complexity=7,
            budget=request.budget
        )
        
        # 3. Код-ревью
        print(f"🔍 Running code review...")
        review = router.route(
            prompt=f"""Review this generated code:

CODE:
{code['response'][:2000]}...

Check for:
1. Security issues
2. Best practices
3. Performance concerns
4. Missing error handling

Provide brief summary with score (0-100).""",
            task_type='review',
            complexity=5,
            budget='cheap'
        )
        
        # Формирование ответа
        project_id = f"proj_{hash(request.idea) % 100000:05d}"
        total_cost = (
            architecture.get('cost', 0) + 
            code.get('cost', 0) + 
            review.get('cost', 0)
        )
        
        return ProjectResponse(
            project_id=project_id,
            architecture=architecture,
            code=code,
            review=review,
            total_cost=total_cost,
            status="completed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Получить статистику использования AI моделей
    
    Возвращает:
    - Общее количество запросов
    - Использованные токены
    - Затраченные средства
    - Статистику по каждой модели
    - Доступность моделей
    """
    try:
        stats = router.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка состояния сервиса
    
    Проверяет:
    - Доступность AI моделей
    - Статистику использования
    - Общее состояние системы
    - Версию API
    - Статус базы данных
    """
    try:
        available = router._get_available_models()
        stats = router.get_stats()
        
        # Проверка доступности базы данных
        db_status = "healthy"
        try:
            db = get_db()
            # Простая проверка соединения через простой запрос
            with sqlite3.connect(db.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        return HealthResponse(
            status="healthy",
            services={
                "anthropic": available['claude'],
                "openai": available['openai'],
                "openrouter": available['openrouter'],
                "gemini": available['gemini'],
                "ollama": available['ollama'],
                "database": db_status
            },
            router_stats={
                "total_calls": stats['calls'],
                "total_cost": stats['cost'],
                "api_version": app.version
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def list_models():
    """
    Список всех доступных моделей и их статус
    """
    available = router._get_available_models()
    
    models_info = {
        "claude": {
            "name": "Claude Sonnet 4.5",
            "available": available['claude'],
            "use_cases": ["architecture", "research", "complex_code"],
            "cost": "$$$ (Premium)"
        },
        "openai": {
            "name": "GPT-4 Turbo",
            "available": available['openai'],
            "use_cases": ["code", "test", "general"],
            "cost": "$$ (Medium)"
        },
        "openrouter": {
            "name": "DeepSeek V3",
            "available": available['openrouter'],
            "use_cases": ["code", "devops", "review"],
            "cost": "$ (Cheap)"
        },
        "gemini": {
            "name": "Gemini 2.0 Flash",
            "available": available['gemini'],
            "use_cases": ["review", "quick_code", "validation"],
            "cost": "FREE"
        },
        "ollama": {
            "name": "Ollama (Local)",
            "available": available['ollama'],
            "use_cases": ["offline", "private", "unlimited"],
            "cost": "FREE (Local)"
        }
    }
    
    return models_info


# ============================================
# Monitoring Endpoints
# ============================================

@app.get("/api/metrics")
async def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """
    Получить метрики системы

    Args:
    - name: Имя метрики для фильтрации
    - start_time: Начало периода (ISO format)
    - end_time: Конец периода (ISO format)

    Returns:
    - metrics: Список метрик
    - summary: Сводная статистика
    """
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    metrics = metrics_collector.get_metrics(name, start, end)
    summary = metrics_collector.get_summary()

    return {
        "metrics": [m.to_dict() for m in metrics[-1000:]],  # Last 1000 metrics
        "summary": summary
    }


@app.get("/api/alerts")
async def get_alerts(
    active_only: bool = False,
    limit: int = 100
):
    """
    Получить алерты системы

    Args:
    - active_only: Показывать только активные алерты
    - limit: Максимальное количество алертов

    Returns:
    - alerts: Список алертов
    - active_count: Количество активных алертов
    """
    if active_only:
        alerts = alert_manager.get_active_alerts()
    else:
        alerts = alert_manager.get_alert_history(limit)

    return {
        "alerts": [a.to_dict() for a in alerts],
        "active_count": len(alert_manager.get_active_alerts())
    }


@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Отметить алерт как решенный

    Args:
    - alert_id: ID алерта

    Returns:
    - resolved: True если успешно
    """
    alert_manager.resolve_alert(alert_id)
    return {"resolved": True}


@app.get("/api/system-status")
async def get_system_status():
    """
    Получить полный статус системы

    Returns:
    - health: Статус здоровья
    - metrics: Ключевые метрики
    - alerts: Активные алерты
    - performance: Производительность
    """
    # Get system metrics
    summary = metrics_collector.get_summary()

    # Calculate average response time
    request_durations = summary.get("histograms", {}).get("http_request_duration_seconds", {})
    avg_response_time = request_durations.get("mean", 0) if request_durations else 0

    # Get error rates
    total_requests = summary.get("counters", {}).get("http_requests_total", 0)
    error_5xx = summary.get("counters", {}).get("http_errors_total{type=5xx}", 0)
    error_4xx = summary.get("counters", {}).get("http_errors_total{type=4xx}", 0)

    error_rate = ((error_5xx + error_4xx) / total_requests * 100) if total_requests > 0 else 0

    # Get system resources
    cpu_percent = summary.get("gauges", {}).get("system_cpu_percent", 0)
    memory_percent = summary.get("gauges", {}).get("system_memory_percent", 0)
    disk_percent = summary.get("gauges", {}).get("system_disk_percent", 0)

    # Determine health status
    health_status = "healthy"
    if error_rate > 10 or cpu_percent > 90 or memory_percent > 90:
        health_status = "degraded"
    if error_rate > 25 or cpu_percent > 95 or memory_percent > 95:
        health_status = "critical"

    return {
        "health": health_status,
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "requests": {
                "total": total_requests,
                "errors_5xx": error_5xx,
                "errors_4xx": error_4xx,
                "error_rate": f"{error_rate:.2f}%"
            },
            "performance": {
                "avg_response_time": f"{avg_response_time:.3f}s",
                "p95_response_time": f"{request_durations.get('p95', 0):.3f}s" if request_durations else "0.000s",
                "p99_response_time": f"{request_durations.get('p99', 0):.3f}s" if request_durations else "0.000s"
            },
            "resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "process_count": summary.get("gauges", {}).get("system_process_count", 0)
            }
        },
        "alerts": {
            "active": len(alert_manager.get_active_alerts()),
            "recent": [a.to_dict() for a in alert_manager.get_active_alerts()[:5]]
        }
    }


@app.get("/api/history", response_model=HistoryResponse)
async def get_history(
    limit: int = 50,
    offset: int = 0,
    model: Optional[str] = None,
    task_type: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Получить историю запросов к AI
    
    Parameters:
    - limit: количество записей (max 100)
    - offset: смещение для пагинации
    - model: фильтр по модели
    - task_type: фильтр по типу задачи
    - search: поиск по тексту
    """
    try:
        db = get_db()
        
        # Ограничиваем максимальный limit
        limit = min(limit, 100)
        
        items = db.get_history(
            limit=limit,
            offset=offset,
            model=model,
            task_type=task_type,
            search=search
        )
        
        # Общее количество (для пагинации)
        # Упрощенно - берем из текущих результатов
        total = len(items) + offset
        
        return HistoryResponse(
            total=total,
            items=items,
            page=offset // limit + 1 if limit > 0 else 1,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/stats", response_model=HistoryStatsResponse)
async def get_history_stats():
    """
    Получить статистику по истории запросов
    
    Возвращает:
    - Общую статистику
    - Статистику по моделям
    - Статистику по типам задач
    - Статистику по датам (последние 7 дней)
    """
    try:
        db = get_db()
        stats = db.get_stats()
        return HistoryStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/export")
async def export_history(
    format: str = "json",
    model: Optional[str] = None,
    task_type: Optional[str] = None
):
    """
    Экспорт истории в файл
    
    Parameters:
    - format: json или csv
    - model: фильтр по модели
    - task_type: фильтр по типу задачи
    """
    try:
        import tempfile
        from fastapi.responses import FileResponse
        
        db = get_db()
        
        # Создаем временный файл
        suffix = ".json" if format == "json" else ".csv"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        
        # Экспорт
        if format == "json":
            count = db.export_to_json(
                temp_file.name,
                model=model,
                task_type=task_type
            )
        else:
            count = db.export_to_csv(
                temp_file.name,
                model=model,
                task_type=task_type
            )
        
        filename = f"history_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        
        return FileResponse(
            temp_file.name,
            media_type="application/octet-stream",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# AI Models Ranking Endpoints
# ============================================

@app.get("/api/rankings")
async def get_rankings():
    """
    Получить агрегированные рейтинги всех AI моделей

    Returns:
        Dict с успехом, списком моделей с усредненными оценками и их количеством
    """
    try:
        db = get_db()
        rankings = db.get_all_rankings()
        return {
            "success": True,
            "rankings": rankings,
            "count": len(rankings)
        }
    except Exception as e:
        logger.error(f"Rankings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rankings/{category}")
async def get_rankings_by_category(category: str, limit: int = 3):
    """
    Получить рейтинги для конкретной категории
    
    Parameters:
    - category: reasoning, coding, vision, chat, agents, translation, local
    - limit: количество моделей (default: 3)
    """
    try:
        db = get_db()
        rankings = db.get_rankings_by_category(category, limit)
        return {"category": category, "models": rankings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rankings/update")
async def update_rankings():
    """
    Обновить рейтинги (запустить сбор данных)
    
    Returns:
        Статистика обновления по категориям
    """
    try:
        collector = RankingCollector()
        stats = collector.collect_all_rankings()
        
        total = sum(stats.values())
        
        return {
            "success": True,
            "total_updated": total,
            "by_category": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rankings/sources")
async def get_trusted_sources():
    """
    Получить список доверенных источников данных
    """
    try:
        db = get_db()
        sources = db.get_trusted_sources()
        return {"sources": sources, "count": len(sources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Streaming Chat Endpoint
# ============================================

async def stream_chat_response(prompt: str, task_type: str, complexity: int, budget: str, session_id: str = None):
    """
    Генератор для потоковой передачи ответа
    """
    try:
        # Получаем полный ответ от роутера
        result = router.route(
            prompt=prompt,
            task_type=task_type,
            complexity=complexity,
            budget=budget,
            session_id=session_id
        )
        
        # Отправляем метаданные первым сообщением
        metadata = {
            'type': 'metadata',
            'model': result['model'],
            'cost': result['cost'],
            'context_used': result.get('context_used', False),
            'context_length': result.get('context_length', 0)
        }
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # Симулируем streaming - разбиваем ответ на части
        response_text = result['response']
        words = response_text.split()
        
        # Отправляем слова по частям
        for i, word in enumerate(words):
            chunk = word + (' ' if i < len(words) - 1 else '')
            yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"
            await asyncio.sleep(0.05)
        
        # Отправляем сигнал завершения
        yield f"data: {json.dumps({'type': 'done', 'tokens': result['tokens']})}\n\n"
        
        # Сохраняем в историю
        db = get_db()
        db.add_request(
            prompt=prompt,
            response=response_text,
            model=result['model'],
            task_type=task_type,
            complexity=complexity,
            budget=budget,
            tokens=result.get('tokens', 0),
            cost=result.get('cost', 0.0),
            error=result.get('error', False)
        )
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Потоковый чат с AI (Server-Sent Events)
    """
    return StreamingResponse(
        stream_chat_response(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            budget=request.budget,
            session_id=request.session_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest, client_request: Request):
    """
    Регистрация нового пользователя

    Parameters:
    - email: Email пользователя
    - password: Пароль (минимум 8 символов)

    Returns:
    - token: JWT токен
    - user: Информация о пользователе
    """
    # Проверяем rate limiting
    client_ip = client_request.client.host if client_request.client else "unknown"
    rate_limiter = get_rate_limiter()

    if not rate_limiter.check_rate_limit(f"auth_register:{client_ip}", tier="anonymous"):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Please try again later."
        )

    try:
        db = get_db()

        # Проверяем существование пользователя
        existing = db.get_user_by_email(request.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Хэшируем пароль
        password_hash = hash_password(request.password)

        # Создаем пользователя
        user_id = db.create_user(request.email, password_hash)

        # Получаем пользователя
        user = db.get_user_by_email(request.email)

        # Генерируем токен
        token = create_jwt_token(user_id, request.email)

        # Создаем response с cookie
        response = JSONResponse(content={
            "token": token,  # Оставляем для обратной совместимости
            "user": {
                "id": user['id'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else user['created_at']
            },
            "message": "Registration successful"
        })

        # Устанавливаем httpOnly cookie
        secure_cookie = os.getenv("ENVIRONMENT", "development").lower() == "production"
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,  # Защита от XSS
            secure=secure_cookie,  # True в production с HTTPS
            samesite="lax",  # Защита от CSRF
            max_age=86400,  # 24 часа
            path="/"
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, client_request: Request):
    """
    Вход в систему

    Parameters:
    - email: Email пользователя
    - password: Пароль

    Returns:
    - token: JWT токен
    - user: Информация о пользователе
    """
    # Проверяем rate limiting (более строгий для login)
    client_ip = client_request.client.host if client_request.client else "unknown"
    rate_limiter = get_rate_limiter()

    # Используем комбинацию IP + email для защиты от brute force конкретных аккаунтов
    if not rate_limiter.check_rate_limit(f"auth_login:{client_ip}:{request.email}", tier="anonymous"):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later."
        )

    try:
        db = get_db()

        # Получаем пользователя
        user = db.get_user_by_email(request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Проверяем пароль
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Обновляем время последнего входа
        db.update_user_last_login(user['id'])

        # Генерируем токен
        token = create_jwt_token(user['id'], user['email'])

        # Создаем response с cookie
        response = JSONResponse(content={
            "token": token,  # Оставляем для обратной совместимости
            "user": {
                "id": user['id'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else user['created_at']
            },
            "message": "Login successful"
        })

        # Устанавливаем httpOnly cookie
        secure_cookie = os.getenv("ENVIRONMENT", "development").lower() == "production"
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,  # Защита от XSS
            secure=secure_cookie,  # True в production с HTTPS
            samesite="lax",  # Защита от CSRF
            max_age=86400,  # 24 часа
            path="/"
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/refresh")
async def refresh_token(authorization: str = Header(None)):
    """
    Обновить JWT токен (refresh token endpoint)
    
    Использует текущий токен (даже если он почти истек) для получения нового токена.
    
    Headers:
    - Authorization: Bearer {token}
    
    Returns:
    - Новый токен и информация о пользователе
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = authorization.replace("Bearer ", "")
        
        # Проверяем токен (даже если он почти истек, но еще валиден)
        payload = verify_jwt(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Получаем пользователя из базы для подтверждения что он еще существует
        db = get_db()
        user = db.get_user_by_email(payload['email'])
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user.get('is_active', True):
            raise HTTPException(status_code=403, detail="User account is disabled")

        # Генерируем новый токен
        new_token = create_jwt_token(user['id'], user['email'])

        # Создаем response с новым токеном
        secure_cookie = os.getenv("ENVIRONMENT", "development").lower() == "production"
        response = JSONResponse(content={
            "token": new_token,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "created_at": user['created_at'].isoformat() if isinstance(user.get('created_at'), datetime) else user.get('created_at')
            },
            "message": "Token refreshed successfully"
        })

        # Устанавливаем новый токен в cookie
        response.set_cookie(
            key="auth_token",
            value=new_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=86400,  # 24 часа
            path="/"
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me", response_model=UserInfo)
async def get_current_user(authorization: str = Header(None)):
    """
    Получить информацию о текущем пользователе (protected endpoint)

    Headers:
    - Authorization: Bearer {token}

    Returns:
    - Информация о пользователе
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = authorization.replace("Bearer ", "")
        payload = verify_jwt(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        db = get_db()
        user = db.get_user_by_email(payload['email'])

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return UserInfo(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
async def logout():
    """
    Выход из системы (очистка cookie)
    """
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="auth_token", path="/")
    return response


@app.get("/api/auth/csrf-token")
async def get_csrf_token(authorization: str = Header(None)):
    """
    Получить CSRF токен для защищенных операций

    Returns:
    - csrf_token: Токен для использования в заголовке X-CSRF-Token
    """
    # Проверяем авторизацию
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Генерируем CSRF токен
    csrf = get_csrf_protection()
    csrf_token = csrf.generate_token(str(payload.get('sub', '')))

    return {
        "csrf_token": csrf_token,
        "header_name": "X-CSRF-Token",
        "expires_in": 3600
    }


# ============================================
# OAuth Endpoints
# ============================================

@app.get("/api/auth/oauth/providers")
async def get_oauth_providers():
    """
    Получить список доступных OAuth провайдеров

    Returns:
    - providers: Список доступных провайдеров для входа
    """
    providers = oauth_manager.list_available_providers()
    return {
        "providers": [
            {
                "name": provider,
                "display_name": provider.capitalize(),
                "icon_url": f"/static/icons/{provider}.svg"
            }
            for provider in providers
        ]
    }


@app.get("/api/auth/oauth/{provider}/login")
async def oauth_login(provider: str):
    """
    Инициировать OAuth вход для указанного провайдера

    Args:
    - provider: Имя провайдера (google, github, microsoft)

    Returns:
    - authorization_url: URL для редиректа пользователя
    """
    oauth_provider = oauth_manager.get_provider(provider)
    if not oauth_provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider {provider} is not configured"
        )

    # Генерируем state для защиты от CSRF
    state = oauth_provider.generate_state()

    # Получаем URL авторизации
    auth_url = oauth_provider.get_authorization_url(state=state)

    return {
        "authorization_url": auth_url,
        "state": state
    }


@app.post("/api/auth/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    response: Response
):
    """
    Обработать OAuth callback от провайдера

    Args:
    - provider: Имя провайдера
    - code: Код авторизации от провайдера
    - state: State параметр для проверки CSRF

    Returns:
    - user: Информация о пользователе
    - access_token: JWT токен для API
    """
    try:
        # Обрабатываем callback
        result = await oauth_manager.handle_callback(provider, code, state)

        # Извлекаем данные пользователя
        user_info = result["user_info"]
        email = user_info.get("email") or user_info.get("mail")
        name = user_info.get("name") or user_info.get("displayName") or user_info.get("login")

        if not email:
            raise HTTPException(
                status_code=400,
                detail="Email not provided by OAuth provider"
            )

        db = get_db()

        # Проверяем, существует ли пользователь
        existing_user = db.get_user_by_email(email)

        if existing_user:
            # Обновляем информацию о последнем входе
            user_id = existing_user["id"]
            db.execute_query(
                """
                UPDATE users
                SET last_login = CURRENT_TIMESTAMP,
                    oauth_provider = ?,
                    oauth_id = ?
                WHERE id = ?
                """,
                (provider, user_info.get("id", ""), user_id)
            )
        else:
            # Создаем нового пользователя
            user_id = db.create_user(
                email=email,
                password_hash="",  # OAuth пользователи не имеют пароля
                username=name or email.split("@")[0],
                oauth_provider=provider,
                oauth_id=user_info.get("id", "")
            )

        # Создаем JWT токен
        token = create_jwt_token({
            "user_id": user_id,
            "email": email,
            "provider": provider
        })

        # Устанавливаем cookie
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400  # 24 часа
        )

        return {
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "provider": provider
            },
            "access_token": token,
            "token_type": "bearer"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process OAuth callback"
        )


# ============================================
# CSRF Protection Dependency
# ============================================

async def verify_csrf_token(
    x_csrf_token: str = Header(None),
    authorization: str = Header(None)
):
    """Dependency для проверки CSRF токена"""
    # Проверяем наличие CSRF токена
    if not x_csrf_token:
        raise HTTPException(
            status_code=403,
            detail="CSRF token required. Get one from /api/auth/csrf-token"
        )

    # Проверяем авторизацию
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    # Проверяем CSRF токен
    csrf = get_csrf_protection()
    if not csrf.verify_token(x_csrf_token, str(payload.get('sub', ''))):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    return payload


# ============================================
# Two-Factor Authentication Endpoints
# ============================================

# Initialize 2FA manager
two_factor = TwoFactorAuth(get_db())

@app.post("/api/auth/2fa/setup")
async def setup_2fa(
    authorization: str = Header(None),
    x_csrf_token: str = Header(None)
):
    """
    Начать настройку 2FA для пользователя

    Returns:
    - qr_code: Base64 QR код для сканирования
    - secret: Секретный ключ для ручного ввода
    - backup_codes: Резервные коды
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify CSRF token
    csrf = get_csrf_protection()
    if not csrf.verify_token(x_csrf_token, str(payload.get('sub', ''))):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user_id = payload.get('sub')
    email = payload.get('email', '')

    # Generate 2FA setup
    setup_data = two_factor.generate_secret(user_id, email)

    return {
        "qr_code": f"data:image/png;base64,{setup_data['qr_code']}",
        "secret": setup_data['manual_entry_key'],
        "backup_codes": setup_data['backup_codes']
    }


@app.post("/api/auth/2fa/enable")
async def enable_2fa(
    token: str,
    authorization: str = Header(None),
    x_csrf_token: str = Header(None)
):
    """
    Включить 2FA после проверки токена

    Args:
    - token: 6-значный TOTP токен

    Returns:
    - enabled: True если 2FA успешно включена
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    jwt_token = authorization.replace("Bearer ", "")
    payload = verify_jwt(jwt_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify CSRF token
    csrf = get_csrf_protection()
    if not csrf.verify_token(x_csrf_token, str(payload.get('sub', ''))):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user_id = payload.get('sub')

    # Enable 2FA
    if two_factor.enable_2fa(user_id, token):
        return {"enabled": True, "message": "2FA has been enabled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid token or 2FA setup not found")


@app.post("/api/auth/2fa/disable")
async def disable_2fa(
    password: str,
    authorization: str = Header(None),
    x_csrf_token: str = Header(None)
):
    """
    Отключить 2FA

    Args:
    - password: Пароль пользователя для подтверждения

    Returns:
    - disabled: True если 2FA успешно отключена
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify CSRF token
    csrf = get_csrf_protection()
    if not csrf.verify_token(x_csrf_token, str(payload.get('sub', ''))):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user_id = payload.get('sub')
    email = payload.get('email')

    # Verify password
    db = get_db()
    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user['password_hash']):
        raise HTTPException(status_code=403, detail="Invalid password")

    # Disable 2FA
    if two_factor.disable_2fa(user_id):
        return {"disabled": True, "message": "2FA has been disabled"}
    else:
        raise HTTPException(status_code=400, detail="Failed to disable 2FA")


@app.post("/api/auth/2fa/verify")
async def verify_2fa(
    token: str,
    user_id: int,
    request: Request
):
    """
    Проверить 2FA токен при входе

    Args:
    - token: TOTP токен или резервный код
    - user_id: ID пользователя

    Returns:
    - valid: True если токен валиден
    """
    # Get IP address
    ip_address = request.client.host if request.client else None

    # Check rate limiting
    if not two_factor.check_rate_limit(user_id, ip_address):
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Please try again later."
        )

    # Verify token
    if two_factor.verify_token(user_id, token, ip_address):
        return {"valid": True}
    else:
        raise HTTPException(status_code=403, detail="Invalid 2FA token")


@app.get("/api/auth/2fa/backup-codes")
async def get_backup_codes(
    authorization: str = Header(None)
):
    """
    Получить оставшиеся резервные коды

    Returns:
    - backup_codes: Список резервных кодов
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get('sub')

    # Get backup codes
    codes = two_factor.get_backup_codes(user_id)

    return {"backup_codes": codes}


@app.post("/api/auth/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(
    authorization: str = Header(None),
    x_csrf_token: str = Header(None)
):
    """
    Сгенерировать новые резервные коды

    Returns:
    - backup_codes: Новые резервные коды
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Verify CSRF token
    csrf = get_csrf_protection()
    if not csrf.verify_token(x_csrf_token, str(payload.get('sub', ''))):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user_id = payload.get('sub')

    # Regenerate codes
    new_codes = two_factor.regenerate_backup_codes(user_id)

    return {"backup_codes": new_codes}


@app.get("/api/auth/2fa/status")
async def get_2fa_status(
    authorization: str = Header(None)
):
    """
    Проверить статус 2FA для пользователя

    Returns:
    - enabled: True если 2FA включена
    - recent_attempts: Последние попытки входа
    """
    # Verify authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get('sub')

    # Get 2FA status
    enabled = two_factor.is_2fa_enabled(user_id)
    recent_attempts = two_factor.get_recent_attempts(user_id) if enabled else []

    return {
        "enabled": enabled,
        "recent_attempts": recent_attempts
    }


# ============================================
# Schema Validation Helpers
# ============================================

def validate_record_data(data: Dict[str, Any], schema: DatabaseSchema) -> None:
    """
    Validate record data against database schema

    Args:
        data: Record data to validate
        schema: Database schema

    Raises:
        HTTPException: If validation fails
    """
    from datetime import datetime as dt

    # Check required fields
    for column in schema.columns:
        if column.required and column.name not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Required field '{column.name}' is missing"
            )

    # Validate each field
    for field_name, field_value in data.items():
        # Skip system fields
        if field_name in ['id', 'created_at', 'updated_at']:
            continue

        # Find column definition
        column = next((col for col in schema.columns if col.name == field_name), None)
        if not column:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown field '{field_name}' not in schema"
            )

        # Skip validation for None values in optional fields
        if field_value is None and not column.required:
            continue

        # Type validation
        if column.type == 'text':
            if not isinstance(field_value, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be a string (got {type(field_value).__name__})"
                )
            # Length validation
            if column.min_length is not None and len(field_value) < column.min_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be at least {column.min_length} characters long (got {len(field_value)})"
                )
            if column.max_length is not None and len(field_value) > column.max_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be at most {column.max_length} characters long (got {len(field_value)})"
                )

        elif column.type == 'number':
            if not isinstance(field_value, (int, float)):
                # Try to parse string to number
                if isinstance(field_value, str):
                    try:
                        field_value = float(field_value)
                        # Update the data dict with parsed value
                        data[field_name] = field_value
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field_name}' must be a number (got '{field_value}')"
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field_name}' must be a number (got {type(field_value).__name__})"
                    )
            # Range validation
            if column.min_value is not None and field_value < column.min_value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be at least {column.min_value} (got {field_value})"
                )
            if column.max_value is not None and field_value > column.max_value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be at most {column.max_value} (got {field_value})"
                )

        elif column.type == 'boolean':
            if not isinstance(field_value, bool):
                # Try to parse string to boolean
                if isinstance(field_value, str):
                    if field_value.lower() in ('true', '1', 'yes'):
                        data[field_name] = True
                    elif field_value.lower() in ('false', '0', 'no'):
                        data[field_name] = False
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Field '{field_name}' must be a boolean (got '{field_value}'). Use true/false"
                        )
                elif isinstance(field_value, (int, float)):
                    data[field_name] = bool(field_value)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field_name}' must be a boolean (got {type(field_value).__name__})"
                    )

        elif column.type == 'date':
            if not isinstance(field_value, str):
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be a date string in YYYY-MM-DD format (got {type(field_value).__name__})"
                )
            # Validate date format
            try:
                parsed_date = dt.strptime(field_value, '%Y-%m-%d')
                # Validate reasonable date range (1900-2100)
                if parsed_date.year < 1900 or parsed_date.year > 2100:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Field '{field_name}' date must be between 1900 and 2100 (got {parsed_date.year})"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be in YYYY-MM-DD format (got '{field_value}'). Example: 2025-01-15"
                )

        elif column.type == 'select':
            if not column.options:
                raise HTTPException(
                    status_code=500,
                    detail=f"Field '{field_name}' is select type but has no options defined"
                )
            if field_value not in column.options:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field_name}' must be one of: {', '.join(column.options)} (got '{field_value}')"
                )

# ============================================
# JWT Middleware Helper
# ============================================

def get_current_user_from_token(authorization: str = Header(None)) -> Dict:
    """
    Dependency для получения текущего пользователя из JWT токена

    Usage:
    ```python
    @app.get("/api/protected")
    async def protected_route(current_user: Dict = Depends(get_current_user_from_token)):
        return {"message": f"Hello {current_user['email']}!"}
    ```
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    payload = verify_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Add user_id field for compatibility
    payload['user_id'] = payload['sub']

    return payload


# ============================================
# Rate Limiting Dependency
# ============================================

async def check_rate_limit(
    request: Request,
    authorization: str = Header(None)
):
    """
    Rate limiting dependency - проверяет лимиты запросов

    Usage:
    ```python
    @app.get("/api/endpoint", dependencies=[Depends(check_rate_limit)])
    async def endpoint():
        return {"data": "..."}
    ```
    """
    limiter = get_rate_limiter()

    # Определяем идентификатор и tier
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        payload = verify_jwt(token)
        if payload:
            identifier = f"user_{payload['sub']}"
            tier = 'authenticated'
        else:
            # Invalid token - use IP
            identifier = request.client.host if request.client else "unknown"
            tier = 'anonymous'
    else:
        # No token - use IP address
        identifier = request.client.host if request.client else "unknown"
        tier = 'anonymous'

    # Проверяем rate limit
    if not limiter.check_rate_limit(identifier, tier):
        # Получаем информацию для заголовков
        remaining = limiter.get_remaining(identifier, tier)
        reset_time = limiter.get_reset_time(identifier, tier)

        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down.",
            headers={
                "X-RateLimit-Limit": "100" if tier == 'authenticated' else "10",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time)
            }
        )

    # Rate limit OK - добавляем заголовки для информации
    remaining = limiter.get_remaining(identifier, tier)
    # Headers будут добавлены в middleware
    request.state.rate_limit_remaining = remaining


# Example of protected endpoint
@app.get("/api/protected-example")
async def protected_route_example(current_user: Dict = Depends(get_current_user_from_token)):
    """
    Пример защищенного эндпоинта

    Требует валидный JWT токен в заголовке Authorization
    """
    return {
        "message": f"Hello {current_user['email']}!",
        "user_id": current_user['id'],
        "member_since": current_user['created_at']
    }

# ============================================
# Session Management Endpoints
# ============================================

@app.post("/api/sessions/create")
async def create_session(current_user = Depends(get_current_user)):
    """Создать новую чат-сессию для авторизованного пользователя"""
    try:
        db = get_db()
        session_id = db.create_session(user_id=current_user['id'])
        return {"session_id": session_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user = Depends(get_current_user)):
    """Получить все сообщения сессии (только для владельца)"""
    try:
        db = get_db()
        # Проверяем, принадлежит ли сессия пользователю
        if not db.session_belongs_to_user(session_id, current_user['id']):
            raise HTTPException(status_code=403, detail="Access denied to this session")
        messages = db.get_session_messages(session_id)
        return {"session_id": session_id, "messages": messages, "count": len(messages)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
async def get_all_sessions(current_user = Depends(get_current_user)):
    """Получить список всех сессий пользователя"""
    try:
        db = get_db()
        sessions = db.get_user_sessions(current_user['id'])
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user = Depends(get_current_user)):
    """Удалить сессию (только для владельца)"""
    try:
        db = get_db()
        # Проверяем, принадлежит ли сессия пользователю
        if not db.session_belongs_to_user(session_id, current_user['id']):
            raise HTTPException(status_code=403, detail="Access denied to this session")
        db.delete_session(session_id)
        return {"success": True, "message": f"Session {session_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Projects Management Endpoints
# ============================================

@app.post("/api/projects", response_model=ProjectDetail)
async def create_project(
    request: ProjectCreate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Создать новый проект

    Требуется JWT аутентификация.

    Args:
        request: Данные проекта (name, description)
        token_data: Данные токена (user_id)

    Returns:
        ProjectDetail: Созданный проект
    """
    try:
        db = get_db()
        logger.info(f"Creating project '{request.name}' for user {token_data['user_id']}")

        project_id = db.create_project(
            user_id=token_data['user_id'],
            name=request.name,
            description=request.description
        )

        project = db.get_project(project_id, token_data['user_id'])
        if not project:
            raise HTTPException(status_code=500, detail="Failed to create project")

        # Add database count
        project['database_count'] = 0  # New project has no databases yet

        logger.info(f"Project created successfully: ID={project_id}")
        return ProjectDetail(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects", response_model=List[ProjectDetail])
async def list_projects(token_data: dict = Depends(get_current_user_from_token)):
    """
    Получить список всех проектов пользователя

    Требуется JWT аутентификация.

    Args:
        token_data: Данные токена (user_id)

    Returns:
        List[ProjectDetail]: Список проектов
    """
    try:
        db = get_db()
        logger.info(f"Fetching projects for user {token_data['user_id']}")

        projects = db.get_projects(token_data['user_id'])

        # Add database count for each project
        result = []
        for project in projects:
            databases = db.get_databases(project['id'])
            project['database_count'] = len(databases)
            result.append(ProjectDetail(**project))

        logger.info(f"Found {len(result)} projects")
        return result
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}", response_model=ProjectDetail)
async def get_project_detail(
    project_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить детали конкретного проекта

    Требуется JWT аутентификация.

    Args:
        project_id: ID проекта
        token_data: Данные токена (user_id)

    Returns:
        ProjectDetail: Детали проекта
    """
    try:
        db = get_db()
        logger.info(f"Fetching project {project_id} for user {token_data['user_id']}")

        project = db.get_project(project_id, token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Add database count
        databases = db.get_databases(project['id'])
        project['database_count'] = len(databases)

        return ProjectDetail(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    request: ProjectUpdate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Обновить проект

    Требуется JWT аутентификация.

    Args:
        project_id: ID проекта
        request: Новые данные (name, description)
        token_data: Данные токена (user_id)

    Returns:
        ProjectDetail: Обновленный проект
    """
    try:
        db = get_db()
        logger.info(f"Updating project {project_id} for user {token_data['user_id']}")

        # Проверяем существование проекта
        existing = db.get_project(project_id, token_data['user_id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")

        # Обновляем только переданные поля
        name = request.name if request.name is not None else existing['name']
        description = request.description if request.description is not None else existing.get('description')

        success = db.update_project(
            project_id=project_id,
            user_id=token_data['user_id'],
            name=name,
            description=description
        )

        if not success:
            raise HTTPException(status_code=404, detail="Project not found or update failed")

        # Получаем обновленный проект
        project = db.get_project(project_id, token_data['user_id'])
        databases = db.get_databases(project['id'])
        project['database_count'] = len(databases)

        logger.info(f"Project {project_id} updated successfully")
        return ProjectDetail(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Удалить проект

    Требуется JWT аутентификация.
    Также удаляет все связанные базы данных и записи.

    Args:
        project_id: ID проекта
        token_data: Данные токена (user_id)

    Returns:
        dict: Статус операции
    """
    try:
        db = get_db()
        logger.info(f"Deleting project {project_id} for user {token_data['user_id']}")

        # Проверяем существование
        existing = db.get_project(project_id, token_data['user_id'])
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")

        # Удаляем все базы данных проекта (cascade)
        databases = db.get_databases(project_id)
        for database in databases:
            db.delete_database(database['id'])

        # Удаляем проект
        success = db.delete_project(project_id, token_data['user_id'])
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")

        logger.info(f"Project {project_id} deleted successfully")
        return {"success": True, "message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Databases Management Endpoints
# ============================================

@app.post("/api/databases", response_model=DatabaseResponse)
async def create_database(
    request: DatabaseCreate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Создать новую базу данных в проекте

    Args:
        request: Данные базы данных (project_id, name, schema)
        token_data: Данные токена

    Returns:
        DatabaseResponse: Созданная база данных
    """
    try:
        db = get_db()

        # Verify project belongs to user
        project = db.get_project(request.project_id, token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Convert schema to DatabaseSchema if it's a list
        if isinstance(request.schema, list):
            # Test sends schema as list of dicts like [{'name': 'name', 'type': 'text'}]
            columns = [ColumnDefinition(**col) if isinstance(col, dict) else col for col in request.schema]
            schema_obj = DatabaseSchema(columns=columns)
        else:
            schema_obj = request.schema

        # Validate schema - check for duplicate column names
        column_names = [col.name for col in schema_obj.columns]
        if len(column_names) != len(set(column_names)):
            raise HTTPException(status_code=400, detail="Duplicate column names in schema")

        # Check select type columns have options
        for col in schema_obj.columns:
            if col.type == 'select' and not col.options:
                raise HTTPException(
                    status_code=400,
                    detail=f"Column '{col.name}' is select type but has no options"
                )

        logger.info(f"Creating database '{request.name}' in project {request.project_id}")

        # Store schema as JSON
        schema_json = json.dumps(schema_obj.model_dump())
        database_id = db.create_database(request.project_id, request.name, schema_json)

        # Retrieve created database
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=500, detail="Failed to create database")

        # Parse schema and add record count
        schema_data = json.loads(database['schema_json'])
        database['schema'] = DatabaseSchema(**schema_data)
        database['record_count'] = 0

        logger.info(f"Database created successfully: ID={database_id}")
        return DatabaseResponse(**database)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/databases", response_model=List[DatabaseResponse])
async def list_databases(
    project_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить список всех баз данных проекта

    Args:
        project_id: ID проекта
        token_data: Данные токена

    Returns:
        List[DatabaseResponse]: Список баз данных
    """
    try:
        db = get_db()

        # Verify project belongs to user
        project = db.get_project(project_id, token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        logger.info(f"Fetching databases for project {project_id}")
        databases = db.get_databases(project_id)

        result = []
        for database in databases:
            # Parse schema
            schema_data = json.loads(database['schema_json'])
            database['schema'] = DatabaseSchema(**schema_data)

            # Add record count
            records = db.get_records(database['id'])
            database['record_count'] = len(records)

            result.append(DatabaseResponse(**database))

        logger.info(f"Found {len(result)} databases")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/databases/{database_id}", response_model=DatabaseResponse)
async def get_database_detail(
    database_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить детали конкретной базы данных

    Args:
        database_id: ID базы данных
        token_data: Данные токена

    Returns:
        DatabaseResponse: Детали базы данных
    """
    try:
        db = get_db()

        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        # Verify project belongs to user
        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Parse schema
        schema_data = json.loads(database['schema_json'])
        database['schema'] = DatabaseSchema(**schema_data)

        # Add record count
        records = db.get_records(database['id'])
        database['record_count'] = len(records)

        return DatabaseResponse(**database)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/databases/{database_id}")
async def delete_database(
    database_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Удалить базу данных

    Args:
        database_id: ID базы данных
        token_data: Данные токена

    Returns:
        dict: Статус операции
    """
    try:
        db = get_db()

        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        # Verify project belongs to user
        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        logger.info(f"Deleting database {database_id}")
        success = db.delete_database(database_id)

        if not success:
            raise HTTPException(status_code=404, detail="Database not found")

        logger.info(f"Database {database_id} deleted successfully")
        return {"success": True, "message": "Database deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Database Records Management Endpoints
# ============================================

@app.post("/api/records", response_model=RecordResponse)
async def create_record_simple(
    request: RecordCreate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Создать новую запись в базе данных (упрощенный endpoint)

    Args:
        request: Данные записи с database_id
        token_data: Данные токена

    Returns:
        RecordResponse: Созданная запись
    """
    if not request.database_id:
        raise HTTPException(status_code=400, detail="database_id is required")

    # Redirect to the main endpoint
    return await create_record(request.database_id, request, token_data)

@app.post("/api/databases/{database_id}/records", response_model=RecordResponse)
async def create_record(
    database_id: int,
    request: RecordCreate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Создать новую запись в базе данных

    Args:
        database_id: ID базы данных
        request: Данные записи
        token_data: Данные токена

    Returns:
        RecordResponse: Созданная запись
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Parse schema
        schema_data = json.loads(database['schema_json'])
        schema = DatabaseSchema(**schema_data)

        # Validate record data against schema
        validate_record_data(request.data, schema)

        logger.info(f"Creating record in database {database_id}")

        # Store record as JSON
        data_json = json.dumps(request.data)
        record_id = db.create_record(database_id, data_json)

        # Retrieve created record
        record = db.get_record(record_id)
        if not record:
            raise HTTPException(status_code=500, detail="Failed to create record")

        # Parse data
        record['data'] = json.loads(record['data_json'])

        logger.info(f"Record created successfully: ID={record_id}")
        return RecordResponse(**record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/databases/{database_id}/records", response_model=List[RecordResponse])
async def list_records(
    database_id: int,
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = 'asc',
    filter_field: Optional[str] = None,
    filter_value: Optional[str] = None,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить список записей базы данных с поиском и фильтрацией

    Args:
        database_id: ID базы данных
        limit: Количество записей (max 100)
        offset: Смещение для пагинации
        search: Поисковый запрос (ищет по всем текстовым полям)
        sort_by: Название поля для сортировки
        sort_order: Порядок сортировки (asc/desc)
        filter_field: Поле для фильтрации
        filter_value: Значение для фильтрации
        token_data: Данные токена

    Returns:
        List[RecordResponse]: Список записей
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Parse schema for validation
        schema_data = json.loads(database['schema_json'])
        schema = DatabaseSchema(**schema_data)

        # Enforce limit cap
        if limit > 100:
            limit = 100

        logger.info(f"Fetching records from database {database_id} with search='{search}', filter={filter_field}={filter_value}")

        # Get all records (we'll filter in memory for now)
        # TODO: Move filtering to database layer for better performance
        all_records = db.get_records(database_id, limit=1000, offset=0)

        result = []
        for record in all_records:
            # Parse data
            record['data'] = json.loads(record['data_json'])

            # Apply search filter
            if search:
                search_lower = search.lower()
                found = False
                for col in schema.columns:
                    if col.type == 'text' and col.name in record['data']:
                        field_value = str(record['data'][col.name])
                        if search_lower in field_value.lower():
                            found = True
                            break
                if not found:
                    continue

            # Apply field filter
            if filter_field and filter_value:
                if filter_field not in record['data']:
                    continue
                record_value = str(record['data'][filter_field])
                # For exact match on select/boolean, partial match on text
                col = next((c for c in schema.columns if c.name == filter_field), None)
                if col:
                    if col.type in ['select', 'boolean', 'date']:
                        if record_value != filter_value:
                            continue
                    elif col.type == 'number':
                        try:
                            if float(record_value) != float(filter_value):
                                continue
                        except ValueError:
                            continue
                    else:  # text
                        if filter_value.lower() not in record_value.lower():
                            continue

            result.append(RecordResponse(**record))

        # Apply sorting
        if sort_by:
            col = next((c for c in schema.columns if c.name == sort_by), None)
            if col:
                def get_sort_key(r):
                    value = r.data.get(sort_by)
                    if value is None:
                        return '' if col.type == 'text' else 0
                    if col.type == 'number':
                        return float(value) if isinstance(value, (int, float)) else 0
                    return str(value)

                result.sort(key=get_sort_key, reverse=(sort_order == 'desc'))

        # Apply pagination
        result = result[offset:offset + limit]

        logger.info(f"Found {len(result)} records after filtering")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching records: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/databases/{database_id}/records/{record_id}", response_model=RecordResponse)
async def get_record_detail(
    database_id: int,
    record_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить конкретную запись

    Args:
        database_id: ID базы данных
        record_id: ID записи
        token_data: Данные токена

    Returns:
        RecordResponse: Детали записи
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Get record
        record = db.get_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        # Verify record belongs to the specified database
        if record['database_id'] != database_id:
            raise HTTPException(status_code=404, detail="Record not found")

        # Parse data
        record['data'] = json.loads(record['data_json'])

        return RecordResponse(**record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/databases/{database_id}/records/{record_id}", response_model=RecordResponse)
async def update_record(
    database_id: int,
    record_id: int,
    request: RecordUpdate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Обновить запись

    Args:
        database_id: ID базы данных
        record_id: ID записи
        request: Новые данные
        token_data: Данные токена

    Returns:
        RecordResponse: Обновленная запись
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Get record
        record = db.get_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        # Verify record belongs to the specified database
        if record['database_id'] != database_id:
            raise HTTPException(status_code=404, detail="Record not found")

        # Parse schema
        schema_data = json.loads(database['schema_json'])
        schema = DatabaseSchema(**schema_data)

        # Validate new data against schema
        validate_record_data(request.data, schema)

        logger.info(f"Updating record {record_id}")

        # Update record
        data_json = json.dumps(request.data)
        success = db.update_record(record_id, data_json)

        if not success:
            raise HTTPException(status_code=404, detail="Record not found")

        # Get updated record
        record = db.get_record(record_id)
        record['data'] = json.loads(record['data_json'])

        logger.info(f"Record {record_id} updated successfully")
        return RecordResponse(**record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/databases/{database_id}/records/{record_id}")
async def delete_record(
    database_id: int,
    record_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Удалить запись

    Args:
        database_id: ID базы данных
        record_id: ID записи
        token_data: Данные токена

    Returns:
        dict: Статус операции
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Get record
        record = db.get_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")

        # Verify record belongs to the specified database
        if record['database_id'] != database_id:
            raise HTTPException(status_code=404, detail="Record not found")

        logger.info(f"Deleting record {record_id}")
        success = db.delete_record(record_id)

        if not success:
            raise HTTPException(status_code=404, detail="Record not found")

        logger.info(f"Record {record_id} deleted successfully")
        return {"success": True, "message": "Record deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CSV Import/Export Endpoints
# ============================================

@app.get("/api/databases/{database_id}/export/csv")
async def export_records_csv(
    database_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Экспортировать записи базы данных в CSV

    Args:
        database_id: ID базы данных
        token_data: Данные токена

    Returns:
        CSV file with records
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Parse schema
        schema_data = json.loads(database['schema_json'])
        schema = DatabaseSchema(**schema_data)

        # Get all records
        records = db.get_records(database_id, limit=10000, offset=0)

        # Create CSV in memory
        output = io.StringIO()

        # Column names from schema
        fieldnames = [col.name for col in schema.columns]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')

        # Write header
        writer.writeheader()

        # Write records
        for record in records:
            data = json.loads(record['data_json'])
            # Only include fields that are in schema
            row = {field: data.get(field, '') for field in fieldnames}
            writer.writerow(row)

        # Get CSV content
        csv_content = output.getvalue()
        output.close()

        logger.info(f"Exported {len(records)} records from database {database_id}")

        # Return as downloadable file
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=database_{database_id}_{database['name']}.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CSVImportRequest(BaseModel):
    """Request model for CSV import"""
    csv_content: str = Field(..., description="CSV content as string")
    skip_header: bool = Field(default=True, description="Skip first row as header")
    overwrite: bool = Field(default=False, description="Overwrite existing records")


@app.post("/api/databases/{database_id}/import/csv")
async def import_records_csv(
    database_id: int,
    request: CSVImportRequest,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Импортировать записи из CSV в базу данных

    Args:
        database_id: ID базы данных
        request: CSV content and options
        token_data: Данные токена

    Returns:
        dict: Import statistics
    """
    try:
        db = get_db()

        # Get database and verify access
        database = db.get_database(database_id)
        if not database:
            raise HTTPException(status_code=404, detail="Database not found")

        project = db.get_project(database['project_id'], token_data['user_id'])
        if not project:
            raise HTTPException(status_code=404, detail="Database not found")

        # Parse schema
        schema_data = json.loads(database['schema_json'])
        schema = DatabaseSchema(**schema_data)

        # Parse CSV
        csv_file = io.StringIO(request.csv_content)
        reader = csv.DictReader(csv_file) if request.skip_header else csv.reader(csv_file)

        imported_count = 0
        error_count = 0
        errors = []

        # Clear existing records if overwrite
        if request.overwrite:
            existing_records = db.get_records(database_id, limit=10000, offset=0)
            for record in existing_records:
                db.delete_record(record['id'])
            logger.info(f"Deleted {len(existing_records)} existing records")

        # Process each row
        for idx, row in enumerate(reader, start=1):
            try:
                if isinstance(row, list):
                    # If not using DictReader, map to column names
                    data = {schema.columns[i].name: row[i] for i in range(min(len(row), len(schema.columns)))}
                else:
                    # DictReader returns dict
                    data = dict(row)

                # Validate and create record
                validate_record_data(data, schema)
                data_json = json.dumps(data)
                db.create_record(database_id, data_json)
                imported_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Row {idx}: {str(e)}")
                if error_count > 10:  # Limit error collection
                    errors.append("... (more errors truncated)")
                    break

        logger.info(f"CSV import complete: {imported_count} imported, {error_count} errors")

        return {
            "success": True,
            "imported": imported_count,
            "errors": error_count,
            "error_details": errors[:10]  # Return first 10 errors
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Workflows Management
# ============================================

@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Создать workflow

    Args:
        workflow: Данные workflow
        token_data: Данные токена

    Returns:
        WorkflowResponse: Созданный workflow
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Convert trigger and actions to JSON
        trigger_json = json.dumps(workflow.trigger.dict())
        actions_json = json.dumps([action.dict() for action in workflow.actions])

        logger.info(f"Creating workflow: {workflow.name} for user {user_id}")

        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflows (user_id, name, trigger_type, trigger_config, actions_json, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                workflow.name,
                workflow.trigger.type,
                trigger_json,
                actions_json,
                1 if workflow.enabled else 0
            ))

            workflow_id = cursor.lastrowid
            conn.commit()

        # Fetch the created workflow
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Failed to create workflow")

        # Parse JSON fields
        trigger_data = json.loads(row['trigger_config']) if row['trigger_config'] else {"type": row['trigger_type'], "config": {}}
        actions_data = json.loads(row['actions_json'])

        logger.info(f"Workflow {workflow_id} created successfully")

        return WorkflowResponse(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            trigger=WorkflowTrigger(**trigger_data),
            actions=[WorkflowAction(**action) for action in actions_data],
            enabled=bool(row['enabled']),
            created_at=row['created_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить список workflows пользователя

    Args:
        token_data: Данные токена

    Returns:
        List[WorkflowResponse]: Список workflows
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))

            rows = cursor.fetchall()

        workflows = []
        for row in rows:
            trigger_data = json.loads(row['trigger_config']) if row['trigger_config'] else {"type": row['trigger_type'], "config": {}}
            actions_data = json.loads(row['actions_json'])

            workflows.append(WorkflowResponse(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                trigger=WorkflowTrigger(**trigger_data),
                actions=[WorkflowAction(**action) for action in actions_data],
                enabled=bool(row['enabled']),
                created_at=row['created_at']
            ))

        logger.info(f"Found {len(workflows)} workflows for user {user_id}")
        return workflows
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить workflow по ID

    Args:
        workflow_id: ID workflow
        token_data: Данные токена

    Returns:
        WorkflowResponse: Данные workflow
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Workflow not found")

        trigger_data = json.loads(row['trigger_config']) if row['trigger_config'] else {"type": row['trigger_type'], "config": {}}
        actions_data = json.loads(row['actions_json'])

        return WorkflowResponse(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            trigger=WorkflowTrigger(**trigger_data),
            actions=[WorkflowAction(**action) for action in actions_data],
            enabled=bool(row['enabled']),
            created_at=row['created_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    workflow: WorkflowUpdate,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Обновить workflow

    Args:
        workflow_id: ID workflow
        workflow: Данные для обновления
        token_data: Данные токена

    Returns:
        WorkflowResponse: Обновленный workflow
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists and belongs to user
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            existing = cursor.fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Build update query
        updates = []
        params = []

        if workflow.name is not None:
            updates.append("name = ?")
            params.append(workflow.name)

        if workflow.trigger is not None:
            updates.append("trigger_type = ?")
            updates.append("trigger_config = ?")
            params.append(workflow.trigger.type)
            params.append(json.dumps(workflow.trigger.dict()))

        if workflow.actions is not None:
            updates.append("actions_json = ?")
            params.append(json.dumps([action.dict() for action in workflow.actions]))

        if workflow.enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if workflow.enabled else 0)

        if not updates:
            # No updates, just return existing
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(workflow_id)
        params.append(user_id)

        logger.info(f"Updating workflow {workflow_id}")

        with sqlite3.connect(db.db_path) as conn:
            conn.execute(f"""
                UPDATE workflows
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            """, tuple(params))
            conn.commit()

        # Fetch updated workflow
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            row = cursor.fetchone()

        trigger_data = json.loads(row['trigger_config']) if row['trigger_config'] else {"type": row['trigger_type'], "config": {}}
        actions_data = json.loads(row['actions_json'])

        logger.info(f"Workflow {workflow_id} updated successfully")

        return WorkflowResponse(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            trigger=WorkflowTrigger(**trigger_data),
            actions=[WorkflowAction(**action) for action in actions_data],
            enabled=bool(row['enabled']),
            created_at=row['created_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Удалить workflow

    Args:
        workflow_id: ID workflow
        token_data: Данные токена

    Returns:
        dict: Статус операции
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists and belongs to user
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                SELECT id FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Workflow not found")

        logger.info(f"Deleting workflow {workflow_id}")

        with sqlite3.connect(db.db_path) as conn:
            # Delete workflow executions first
            conn.execute("DELETE FROM workflow_executions WHERE workflow_id = ?", (workflow_id,))
            # Delete workflow
            conn.execute("DELETE FROM workflows WHERE id = ? AND user_id = ?", (workflow_id, user_id))
            conn.commit()

        logger.info(f"Workflow {workflow_id} deleted successfully")
        return {"success": True, "message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    context: Dict[str, Any] = {},
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Выполнить workflow вручную

    Args:
        workflow_id: ID workflow
        context: Контекст выполнения (опционально)
        token_data: Данные токена

    Returns:
        ExecutionResponse: Результат выполнения
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists and belongs to user
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            workflow_row = cursor.fetchone()

        if not workflow_row:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if not workflow_row['enabled']:
            raise HTTPException(status_code=400, detail="Workflow is disabled")

        logger.info(f"Executing workflow {workflow_id}")

        # Execute workflow using WorkflowEngine
        from agents.workflow_engine import WorkflowEngine

        engine = WorkflowEngine()
        result = engine.execute(workflow_id, context)

        # Get the execution record that was created by the engine
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflow_executions
                WHERE id = ?
            """, (result['execution_id'],))

            execution_row = cursor.fetchone()

        if not execution_row:
            raise HTTPException(status_code=500, detail="Execution not found")

        result_data = json.loads(execution_row['result_json']) if execution_row['result_json'] else None

        logger.info(f"Workflow {workflow_id} executed successfully")

        return ExecutionResponse(
            id=execution_row['id'],
            workflow_id=execution_row['workflow_id'],
            status=execution_row['status'],
            result={"success": result['success'], "results": result.get('results', [])},
            error=execution_row['error'],
            executed_at=execution_row['executed_at']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{workflow_id}/executions", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: int,
    limit: int = 50,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Получить историю выполнений workflow

    Args:
        workflow_id: ID workflow
        limit: Максимальное количество результатов
        token_data: Данные токена

    Returns:
        List[ExecutionResponse]: Список выполнений
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists and belongs to user
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                SELECT id FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Workflow not found")

        # Fetch executions
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflow_executions
                WHERE workflow_id = ?
                ORDER BY executed_at DESC
                LIMIT ?
            """, (workflow_id, min(limit, 100)))

            rows = cursor.fetchall()

        executions = []
        for row in rows:
            result_json = row['result_json']
            result_data = None

            if result_json:
                parsed = json.loads(result_json)
                # Wrap list results in a dict for Pydantic validation
                if isinstance(parsed, list):
                    result_data = {"results": parsed}
                else:
                    result_data = parsed

            executions.append(ExecutionResponse(
                id=row['id'],
                workflow_id=row['workflow_id'],
                status=row['status'],
                result=result_data,
                error=row['error'],
                executed_at=row['executed_at']
            ))

        logger.info(f"Found {len(executions)} executions for workflow {workflow_id}")
        return executions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Webhook Trigger Endpoints
# ============================================

@app.post("/api/webhooks/{workflow_id}/{token}")
async def webhook_trigger(
    workflow_id: int,
    token: str,
    request: Request
):
    """
    Public webhook endpoint for triggering workflows

    Args:
        workflow_id: ID of workflow to trigger
        token: Secret token for authentication (generated per workflow)
        request: FastAPI request object (to access body/headers)

    Returns:
        Execution result

    Example webhook URLs:
        POST https://yourapi.com/api/webhooks/123/abc123def456
        Body: {"event": "payment_completed", "amount": 100}
    """
    try:
        db = get_db()

        # Verify workflow exists and is enabled
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND trigger_type = 'webhook' AND enabled = 1
            """, (workflow_id,))

            workflow_row = cursor.fetchone()

        if not workflow_row:
            raise HTTPException(status_code=404, detail="Webhook workflow not found or disabled")

        # Verify webhook token
        trigger_config = json.loads(workflow_row['trigger_config']) if workflow_row['trigger_config'] else {}
        expected_token = trigger_config.get('webhook_token', '')

        if not expected_token or expected_token != token:
            logger.warning(f"Invalid webhook token for workflow {workflow_id}")
            raise HTTPException(status_code=401, detail="Invalid webhook token")

        # Parse webhook payload
        try:
            body = await request.json()
        except:
            body = {}

        # Get headers
        headers = dict(request.headers)

        # Build context with webhook data
        context = {
            'trigger': 'webhook',
            'webhook': {
                'workflow_id': workflow_id,
                'body': body,
                'headers': headers,
                'method': request.method,
                'url': str(request.url)
            },
            'triggered_at': datetime.now().isoformat()
        }

        logger.info(f"Webhook received for workflow {workflow_id}")

        # Execute workflow
        from agents.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        result = engine.execute(workflow_id, context)

        return {
            "success": result['success'],
            "workflow_id": workflow_id,
            "execution_id": result.get('execution_id'),
            "message": "Webhook processed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/{workflow_id}/webhook-url")
async def get_webhook_url(
    workflow_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Get webhook URL for a workflow

    Args:
        workflow_id: ID of workflow
        token_data: User authentication

    Returns:
        Webhook URL and configuration
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists and belongs to user
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))

            workflow_row = cursor.fetchone()

        if not workflow_row:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Get or generate webhook token
        trigger_config = json.loads(workflow_row['trigger_config']) if workflow_row['trigger_config'] else {}

        if 'webhook_token' not in trigger_config:
            # Generate new token
            import secrets
            webhook_token = secrets.token_urlsafe(32)

            trigger_config['webhook_token'] = webhook_token

            # Update workflow
            with sqlite3.connect(db.db_path) as conn:
                conn.execute("""
                    UPDATE workflows
                    SET trigger_config = ?
                    WHERE id = ?
                """, (json.dumps(trigger_config), workflow_id))
                conn.commit()
        else:
            webhook_token = trigger_config['webhook_token']

        # Build webhook URL (use environment variable or default)
        base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        webhook_url = f"{base_url}/api/webhooks/{workflow_id}/{webhook_token}"

        return {
            "workflow_id": workflow_id,
            "webhook_url": webhook_url,
            "webhook_token": webhook_token,
            "instructions": "POST to this URL with JSON body to trigger the workflow"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflows/{workflow_id}/register-schedule")
async def register_schedule(
    workflow_id: int,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Register a schedule workflow with the scheduler

    Args:
        workflow_id: ID of workflow to register
        token_data: User authentication

    Returns:
        Registration status
    """
    try:
        db = get_db()
        user_id = token_data['user_id']

        # Verify workflow exists, belongs to user, and is schedule type
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ? AND trigger_type = 'schedule'
            """, (workflow_id, user_id))

            workflow_row = cursor.fetchone()

        if not workflow_row:
            raise HTTPException(status_code=404, detail="Schedule workflow not found")

        # Register with scheduler
        from workflow_scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler.register_workflow(dict(workflow_row))

        logger.info(f"Registered schedule workflow {workflow_id}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow registered with scheduler"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows/scheduled-jobs")
async def list_scheduled_jobs(token_data: dict = Depends(get_current_user_from_token)):
    """
    Get list of all scheduled jobs

    Args:
        token_data: User authentication

    Returns:
        List of scheduled jobs
    """
    try:
        from workflow_scheduler import get_scheduler
        scheduler = get_scheduler()

        jobs = scheduler.get_scheduled_jobs()

        return {
            "jobs": jobs,
            "count": len(jobs)
        }

    except Exception as e:
        logger.error(f"Error listing scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# INTEGRATIONS ENDPOINTS
# ============================================

@app.get("/api/integrations", response_model=List[IntegrationInfo])
async def list_integrations(token_data: dict = Depends(get_current_user_from_token)):
    """
    List all available integrations with connection status

    Returns list of integrations (Gmail, Google Drive, Telegram) with:
    - Connection status (connected/disconnected/error)
    - Last sync time if connected
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        # Define available integrations
        integrations = [
            {
                'type': 'gmail',
                'name': 'Gmail',
                'description': 'Send and receive emails via Gmail API',
                'icon': 'mail',
                'requires_oauth': True,
                'status': 'disconnected',
                'last_sync': None
            },
            {
                'type': 'google_drive',
                'name': 'Google Drive',
                'description': 'Upload and manage files in Google Drive',
                'icon': 'hard-drive',
                'requires_oauth': True,
                'status': 'disconnected',
                'last_sync': None
            },
            {
                'type': 'telegram',
                'name': 'Telegram',
                'description': 'Send messages via Telegram bot',
                'icon': 'message-circle',
                'requires_oauth': False,
                'status': 'disconnected',
                'last_sync': None
            }
        ]

        # Check connection status for each integration
        for integration in integrations:
            token = db.get_integration_token(user_id, integration['type'])
            if token:
                integration['status'] = 'connected'
                integration['last_sync'] = token.get('updated_at')

        logger.info(f"Listed {len(integrations)} integrations for user {user_id}")
        return integrations

    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/integrations/connect")
async def connect_integration(
    request: ConnectRequest,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Initiate connection to an integration

    For Gmail/Google Drive: Returns OAuth URL for user authorization
    For Telegram: Saves bot token directly
    """
    try:
        user_id = token_data['user_id']
        integration_type = request.integration_type

        # Validate integration type
        if integration_type not in ['gmail', 'google_drive', 'telegram']:
            raise HTTPException(status_code=400, detail="Invalid integration type")

        # Handle Telegram (direct bot token)
        if integration_type == 'telegram':
            if not request.bot_token:
                raise HTTPException(status_code=400, detail="bot_token required for Telegram")

            db = get_db()
            # Save token (expires in 1 year)
            expires_at = (datetime.now() + timedelta(days=365)).isoformat()

            # Prepare metadata with chat_id if provided
            metadata = {}
            if request.chat_id:
                metadata['chat_id'] = request.chat_id

            db.save_integration_token(
                user_id=user_id,
                integration_type='telegram',
                access_token=request.bot_token,
                refresh_token='',
                expires_at=expires_at,
                metadata=metadata if metadata else None
            )

            logger.info(f"Connected Telegram integration for user {user_id}")
            return {"success": True, "message": "Telegram bot connected successfully"}

        # Handle OAuth integrations (Gmail, Google Drive)
        else:
            # Get OAuth configuration from environment
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')

            if not client_id or not redirect_uri:
                raise HTTPException(
                    status_code=500,
                    detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_REDIRECT_URI environment variables."
                )

            # Scopes based on integration type
            if integration_type == 'gmail':
                scopes = [
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'
                ]
                scope_param = 'https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly'
            else:  # google_drive
                scopes = ['https://www.googleapis.com/auth/drive.file']
                scope_param = 'https://www.googleapis.com/auth/drive.file'

            # Generate state with user_id and integration_type
            # Format: "user_id:integration_type"
            state = f"{user_id}:{integration_type}"

            # Build OAuth URL
            from urllib.parse import urlencode
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': scope_param,
                'state': state,
                'access_type': 'offline',
                'prompt': 'consent'  # Force consent to get refresh token
            }
            oauth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

            logger.info(f"Generated OAuth URL for {integration_type} for user {user_id}")
            return {
                "oauth_url": oauth_url,
                "state": state,
                "message": "Please authorize the application"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/integrations/callback")
async def oauth_callback(code: str, state: str):
    """
    OAuth callback handler

    Exchanges authorization code for access/refresh tokens
    and saves them to the database
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    import json as json_lib

    try:
        logger.info(f"OAuth callback received: code={code[:20]}..., state={state[:20]}...")

        # Get OAuth config from environment
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')

        if not all([client_id, client_secret, redirect_uri]):
            logger.error("Missing Google OAuth configuration")
            return RedirectResponse(
                url="/integrations?error=oauth_config_missing",
                status_code=302
            )

        # Parse state to get user_id and integration_type
        # Format: "user_id:integration_type"
        try:
            user_id_str, integration_type = state.split(':')
            user_id = int(user_id_str)
        except (ValueError, AttributeError):
            logger.error(f"Invalid state parameter: {state}")
            return RedirectResponse(
                url="/integrations?error=invalid_state",
                status_code=302
            )

        # Create OAuth flow
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri]
            }
        }

        # Determine scopes based on integration type
        if integration_type == 'gmail':
            scopes = [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly'
            ]
        elif integration_type == 'google_drive':
            scopes = ['https://www.googleapis.com/auth/drive.file']
        else:
            logger.error(f"Unknown integration type: {integration_type}")
            return RedirectResponse(
                url="/integrations?error=unknown_integration",
                status_code=302
            )

        flow = Flow.from_client_config(
            client_config,
            scopes=scopes,
            redirect_uri=redirect_uri
        )

        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Save tokens to database
        db = get_db()

        # Calculate expiry
        from datetime import datetime, timedelta
        if credentials.expiry:
            expires_at = credentials.expiry.isoformat()
        else:
            # Default to 1 hour
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()

        db.save_integration_token(
            user_id=user_id,
            integration_type=integration_type,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or '',
            expires_at=expires_at
        )

        logger.info(f"Successfully saved {integration_type} tokens for user {user_id}")

        # Redirect to frontend with success
        return RedirectResponse(
            url=f"/integrations?success={integration_type}",
            status_code=302
        )

    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url=f"/integrations?error=oauth_failed",
            status_code=302
        )


@app.post("/api/integrations/disconnect")
async def disconnect_integration(
    integration_type: str,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Disconnect an integration

    Removes stored tokens for the specified integration
    """
    try:
        user_id = token_data['user_id']

        # Validate integration type
        if integration_type not in ['gmail', 'google_drive', 'telegram']:
            raise HTTPException(status_code=400, detail="Invalid integration type")

        db = get_db()
        success = db.delete_integration_token(user_id, integration_type)

        if success:
            logger.info(f"Disconnected {integration_type} for user {user_id}")
            return {
                "success": True,
                "message": f"{integration_type} disconnected successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Integration not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/integrations/test")
async def test_integration(
    integration_type: str,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Test an integration connection

    Attempts to connect to the service and make a simple API call
    to verify the connection works
    """
    try:
        user_id = token_data['user_id']

        # Validate integration type
        if integration_type not in ['gmail', 'google_drive', 'telegram']:
            raise HTTPException(status_code=400, detail="Invalid integration type")

        db = get_db()
        token = db.get_integration_token(user_id, integration_type)

        if not token:
            raise HTTPException(status_code=404, detail="Integration not connected")

        # Try to connect using MCP client
        from agents.mcp_client import MCPClient

        client = MCPClient()

        # Test connection based on integration type
        if integration_type == 'telegram':
            # For Telegram, test with bot token
            try:
                client.connect('telegram', {'bot_token': token['access_token']})
                logger.info(f"Telegram integration test successful for user {user_id}")
                return {
                    "success": True,
                    "message": "Telegram bot connection successful",
                    "integration_type": integration_type
                }
            except Exception as e:
                logger.error(f"Telegram test failed: {e}")
                return {
                    "success": False,
                    "message": f"Connection failed: {str(e)}",
                    "integration_type": integration_type
                }
        else:
            # For Google services, would need full OAuth token
            # For MVP, return simulation
            logger.info(f"{integration_type} test simulated for user {user_id}")
            return {
                "success": True,
                "message": f"{integration_type} connection test simulated (OAuth required for full test)",
                "integration_type": integration_type,
                "note": "In production, this would make a real API call to verify the connection"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DASHBOARD ENDPOINTS
# ============================================

class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    total_projects: int
    active_workflows: int
    connected_integrations: int
    ai_requests_today: int
    ai_requests_week: int
    total_databases: int
    total_records: int


class ActivityItem(BaseModel):
    """Activity feed item"""
    id: int
    type: str  # 'project_created', 'workflow_executed', 'integration_connected', 'ai_request', etc.
    title: str
    description: str
    timestamp: str
    icon: str  # Icon name for frontend


@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(token_data: dict = Depends(get_current_user_from_token)):
    """
    Get dashboard statistics

    Returns counts for:
    - Total projects
    - Active workflows (enabled)
    - Connected integrations
    - AI requests (today and week)
    - Total databases
    - Total records
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        with sqlite3.connect(db.db_path) as conn:
            # Count projects
            cursor = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE user_id = ?",
                (user_id,)
            )
            total_projects = cursor.fetchone()[0]

            # Count active workflows
            cursor = conn.execute(
                "SELECT COUNT(*) FROM workflows WHERE user_id = ? AND enabled = 1",
                (user_id,)
            )
            active_workflows = cursor.fetchone()[0]

            # Count connected integrations
            cursor = conn.execute(
                "SELECT COUNT(*) FROM integration_tokens WHERE user_id = ?",
                (user_id,)
            )
            connected_integrations = cursor.fetchone()[0]

            # Count AI requests today
            today = datetime.now().date().isoformat()
            cursor = conn.execute(
                """SELECT COUNT(*) FROM requests
                   WHERE (user_id = ? OR user_id IS NULL) AND date(timestamp) = date(?)""",
                (user_id, today)
            )
            ai_requests_today = cursor.fetchone()[0]

            # Count AI requests this week
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor = conn.execute(
                """SELECT COUNT(*) FROM requests
                   WHERE (user_id = ? OR user_id IS NULL) AND timestamp >= ?""",
                (user_id, week_ago)
            )
            ai_requests_week = cursor.fetchone()[0]

            # Count total databases
            cursor = conn.execute(
                """SELECT COUNT(*) FROM databases d
                   JOIN projects p ON d.project_id = p.id
                   WHERE p.user_id = ?""",
                (user_id,)
            )
            total_databases = cursor.fetchone()[0]

            # Count total records across all databases
            cursor = conn.execute(
                """SELECT COUNT(*) FROM database_records
                   WHERE database_id IN (
                       SELECT d.id FROM databases d
                       JOIN projects p ON d.project_id = p.id
                       WHERE p.user_id = ?
                   )""",
                (user_id,)
            )
            total_records = cursor.fetchone()[0]

        return DashboardStats(
            total_projects=total_projects,
            active_workflows=active_workflows,
            connected_integrations=connected_integrations,
            ai_requests_today=ai_requests_today,
            ai_requests_week=ai_requests_week,
            total_databases=total_databases,
            total_records=total_records
        )

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/activity", response_model=List[ActivityItem])
async def get_dashboard_activity(
    limit: int = 20,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Get recent activity feed

    Returns recent actions across all modules:
    - Projects created
    - Workflows executed
    - Integrations connected
    - AI requests made
    - Records created

    Sorted by most recent first, limited to 20 items by default
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        activities = []

        with sqlite3.connect(db.db_path) as conn:
            # Get recent projects (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            cursor = conn.execute(
                """SELECT id, name, created_at FROM projects
                   WHERE user_id = ? AND created_at >= ?
                   ORDER BY created_at DESC LIMIT 5""",
                (user_id, thirty_days_ago)
            )
            for row in cursor.fetchall():
                activities.append({
                    'id': row[0],
                    'type': 'project_created',
                    'title': f"Created project: {row[1]}",
                    'description': 'New project created',
                    'timestamp': row[2],
                    'icon': 'Folder'
                })

            # Get recent workflow executions
            cursor = conn.execute(
                """SELECT we.id, w.name, we.executed_at
                   FROM workflow_executions we
                   JOIN workflows w ON we.workflow_id = w.id
                   WHERE w.user_id = ?
                   ORDER BY we.executed_at DESC LIMIT 10""",
                (user_id,)
            )
            for row in cursor.fetchall():
                activities.append({
                    'id': row[0],
                    'type': 'workflow_executed',
                    'title': f"Executed workflow: {row[1]}",
                    'description': 'Workflow ran successfully',
                    'timestamp': row[2],
                    'icon': 'Zap'
                })

            # Get recent integrations
            cursor = conn.execute(
                """SELECT id, integration_type, created_at FROM integration_tokens
                   WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT 5""",
                (user_id,)
            )
            for row in cursor.fetchall():
                integration_name = row[1].replace('_', ' ').title()
                activities.append({
                    'id': row[0],
                    'type': 'integration_connected',
                    'title': f"Connected {integration_name}",
                    'description': 'New integration added',
                    'timestamp': row[2],
                    'icon': 'Plug'
                })

            # Get recent AI requests
            cursor = conn.execute(
                """SELECT id, prompt, timestamp FROM requests
                   WHERE (user_id = ? OR user_id IS NULL)
                   ORDER BY timestamp DESC LIMIT 10""",
                (user_id,)
            )
            for row in cursor.fetchall():
                prompt_preview = row[1][:50] + '...' if len(row[1]) > 50 else row[1]
                activities.append({
                    'id': row[0],
                    'type': 'ai_request',
                    'title': f"AI Request: {prompt_preview}",
                    'description': 'Queried AI model',
                    'timestamp': row[2],
                    'icon': 'MessageSquare'
                })

        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)

        # Limit to requested number
        activities = activities[:limit]

        return activities

    except Exception as e:
        logger.error(f"Error fetching dashboard activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/charts/ai-requests")
async def get_ai_requests_chart(
    days: int = 7,
    token_data: dict = Depends(get_current_user_from_token)
):
    """
    Get AI requests over time for charts

    Returns daily counts for the last N days (default 7)
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        data = []

        with sqlite3.connect(db.db_path) as conn:
            # Get requests grouped by date
            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
            cursor = conn.execute(
                """SELECT date(timestamp) as day, COUNT(*) as count
                   FROM requests
                   WHERE (user_id = ? OR user_id IS NULL) AND date(timestamp) >= date(?)
                   GROUP BY date(timestamp)
                   ORDER BY date(timestamp)""",
                (user_id, start_date)
            )

            for row in cursor.fetchall():
                data.append({
                    'date': row[0],
                    'requests': row[1]
                })

        return {"data": data}

    except Exception as e:
        logger.error(f"Error fetching AI requests chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/charts/model-usage")
async def get_model_usage_chart(token_data: dict = Depends(get_current_user_from_token)):
    """
    Get model usage distribution for pie chart

    Returns count of requests per model
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        data = []

        with sqlite3.connect(db.db_path) as conn:
            # Get requests grouped by model
            cursor = conn.execute(
                """SELECT model, COUNT(*) as count
                   FROM requests
                   WHERE (user_id = ? OR user_id IS NULL)
                   GROUP BY model
                   ORDER BY count DESC""",
                (user_id,)
            )

            for row in cursor.fetchall():
                data.append({
                    'model': row[0] or 'Unknown',
                    'requests': row[1]
                })

        return {"data": data}

    except Exception as e:
        logger.error(f"Error fetching model usage chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/charts/workflow-stats")
async def get_workflow_stats_chart(token_data: dict = Depends(get_current_user_from_token)):
    """
    Get workflow execution statistics for bar chart

    Returns execution counts per workflow
    """
    try:
        user_id = token_data['user_id']
        db = get_db()

        data = []

        with sqlite3.connect(db.db_path) as conn:
            # Get execution counts per workflow
            cursor = conn.execute(
                """SELECT w.name, COUNT(we.id) as count
                   FROM workflows w
                   LEFT JOIN workflow_executions we ON w.id = we.workflow_id
                   WHERE w.user_id = ?
                   GROUP BY w.id, w.name
                   ORDER BY count DESC
                   LIMIT 10""",
                (user_id,)
            )

            for row in cursor.fetchall():
                data.append({
                    'workflow': row[0],
                    'executions': row[1]
                })

        return {"data": data}

    except Exception as e:
        logger.error(f"Error fetching workflow stats chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Запуск сервера
# ============================================

if __name__ == "__main__":
    # Получаем порт из переменной окружения (для Railway/Vercel) или используем 8000 по умолчанию
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting AI Development System API Server...")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"🔍 Health Check: http://localhost:{port}/api/health")
    print(f"🌐 Server running on: http://0.0.0.0:{port}")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
