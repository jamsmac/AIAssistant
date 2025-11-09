"""
FastAPI сервер для AI Development System - Refactored Version
Использует модульные routers вместо монолитного файла
"""
import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from agents.db_pool import db_pool
from agents.cache_manager import get_cache_manager
from api.middleware.csrf import CSRFMiddleware

# Initialize Sentry for error tracking
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("RELEASE_VERSION", "1.0.0")
    )

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "agents"))

# Import routers
from api.routers import (
    auth_router,
    chat_router,
    projects_router,
    workflows_router,
    integrations_router,
    dashboard_router,
    monitoring_router,
    rankings_router,
    history_router,
    models_router,
    users_router,
    projects_stub_router,
    ai_models_stub_router,
)


# Import monitoring
from agents.monitoring import metrics_collector, alert_manager, request_monitor, system_monitor, AlertSeverity

# Setup logging
logger = logging.getLogger(__name__)

TESTING_MODE = os.getenv("TESTING") == "true"

cache_scheduler: Optional[AsyncIOScheduler] = None

# Initialize FastAPI
app = FastAPI(
    title="AI Development System API",
    description="REST API для управления AI агентами и автоматизации разработки",
    version="1.0.0"
)

# Setup CORS - copy improved version from server.py
def validate_origin(origin: str) -> bool:
    """Валидирует origin на соответствие security best practices."""
    if not origin or not isinstance(origin, str):
        return False
    if not (origin.startswith("http://") or origin.startswith("https://")):
        return False
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production" and origin.startswith("http://"):
        if "localhost" not in origin:
            logger.warning(f"Rejected insecure HTTP origin in production: {origin}")
            return False
    dangerous_patterns = ["<", ">", "'", '"', "javascript:", "data:", "vbscript:"]
    for pattern in dangerous_patterns:
        if pattern in origin.lower():
            logger.warning(f"Rejected origin with dangerous pattern '{pattern}': {origin}")
            return False
    return True

def setup_cors_middleware():
    """Настраивает CORS middleware с безопасной конфигурацией."""
    DEFAULT_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
    ]
    CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
    production_origins = []
    if CORS_ORIGINS_ENV:
        raw_origins = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()]
        for origin in raw_origins:
            if validate_origin(origin):
                production_origins.append(origin)
                logger.info(f"Added CORS origin: {origin}")
            else:
                logger.warning(f"Rejected invalid CORS origin: {origin}")
    ALLOWED_ORIGINS = DEFAULT_ORIGINS + production_origins
    logger.info(f"CORS configured with {len(ALLOWED_ORIGINS)} allowed origins")
    return ALLOWED_ORIGINS

ALLOWED_ORIGINS = setup_cors_middleware()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Request-ID"
    ],
    expose_headers=[
        "Content-Length",
        "X-Request-ID",
        "X-Response-Time",
        "X-API-Version"
    ],
    max_age=3600,
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(CSRFMiddleware, allowed_origins=ALLOWED_ORIGINS)

# Security Headers Middleware
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

        # Additional security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # HSTS for production
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

app.add_middleware(SecurityHeadersMiddleware)

# API Version Middleware
class APIVersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = app.version
        response.headers["X-API-Server"] = "AI Assistant Platform"
        return response

app.add_middleware(APIVersionMiddleware)

# Monitoring Middleware
class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            request_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )

            response.headers["X-Response-Time"] = f"{duration:.3f}"

            if duration > 10:
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
            duration = time.time() - start_time
            request_monitor.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration=duration
            )

            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)

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

# Include routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
if not TESTING_MODE:
    app.include_router(projects_router.router)
app.include_router(workflows_router.router)
app.include_router(integrations_router.router)
app.include_router(dashboard_router.router)
app.include_router(monitoring_router.router)
app.include_router(rankings_router.router)
app.include_router(history_router.router)
app.include_router(models_router.router)
app.include_router(users_router.router)
if TESTING_MODE:
    app.include_router(projects_stub_router.router)
    app.include_router(ai_models_stub_router.router)


@app.get("/metrics")
async def metrics_stub() -> PlainTextResponse:
    return PlainTextResponse("# HELP app_requests_total Total requests\n# TYPE app_requests_total counter\napp_requests_total{status='success'} 1\n")


@app.get("/api/metrics")
async def app_metrics_stub() -> dict:
    if TESTING_MODE:
        return {"requests": 1, "errors": 0}
    from api.routers.dashboard_router import metrics_collector

    return {
        "summary": metrics_collector.get_summary(),
    }

# Root endpoint
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "status": "running",
        "message": "AI Development System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    import time
    # Validate security configuration
    from agents.auth import validate_secret_key
    environment = os.getenv("ENVIRONMENT", "development").lower()
    is_production = environment == "production"
    
    secret_key = os.getenv("SECRET_KEY")
    if secret_key:
        is_valid, error_message = validate_secret_key(secret_key, is_production)
        if not is_valid:
            if is_production:
                logger.error(f"SECRET_KEY validation failed: {error_message}")
                raise ValueError(f"Invalid SECRET_KEY: {error_message}")
            else:
                logger.warning(f"SECRET_KEY validation warning: {error_message}")
        else:
            logger.info("SECRET_KEY validated successfully")
    else:
        logger.error("SECRET_KEY is not set. Generate one with: python scripts/generate_secret_key.py")
        if is_production:
            raise ValueError("SECRET_KEY must be set in production environment")
    
    logger.info("Starting AI Development System API")

    # Initialize PostgreSQL connection pool if configuration is provided
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            pool_min_size = int(os.getenv("DB_POOL_MIN_SIZE", "10"))
            pool_max_size = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
            pool_max_queries = int(os.getenv("DB_POOL_MAX_QUERIES", "50000"))
            max_idle_lifetime = float(os.getenv("DB_POOL_MAX_IDLE_SECONDS", "300"))

            await db_pool.initialize(
                dsn=database_url,
                min_size=pool_min_size,
                max_size=pool_max_size,
                max_queries=pool_max_queries,
                max_inactive_connection_lifetime=max_idle_lifetime,
            )
            logger.info(
                "Database connection pool initialized (min_size=%s, max_size=%s)",
                pool_min_size,
                pool_max_size,
            )
        except Exception as exc:
            logger.error("Failed to initialize database pool: %s", exc, exc_info=True)
            if is_production:
                raise
    else:
        logger.warning("DATABASE_URL is not set. Skipping PostgreSQL pool initialization")

    # Schedule periodic cache cleanup
    try:
        cache_manager = get_cache_manager()
        global cache_scheduler
        if cache_scheduler is None:
            cache_scheduler = AsyncIOScheduler()
            cache_scheduler.add_job(
                cache_manager.cleanup_expired,
                "interval",
                hours=int(os.getenv("CACHE_CLEANUP_INTERVAL_HOURS", "6")),
                id="cache_cleanup",
                max_instances=1,
                replace_existing=True,
            )
            cache_scheduler.start()
            logger.info("Cache cleanup scheduler started")
    except Exception as exc:
        logger.error("Failed to start cache cleanup scheduler: %s", exc, exc_info=True)
        if is_production:
            raise

    # Start workflow scheduler
    try:
        from workflow_scheduler import start_scheduler
        start_scheduler()
        logger.info("Workflow scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start workflow scheduler: {e}")

    # Start system monitoring
    import asyncio
    asyncio.create_task(system_monitor.start(interval=60))

    # Initialize alert channels if configured
    if os.getenv("SMTP_HOST"):
        from agents.monitoring import EmailNotificationChannel
        email_channel = EmailNotificationChannel(
            smtp_host=os.getenv("SMTP_HOST"),
            smtp_port=int(os.getenv("SMTP_PORT", 587)),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            to_emails=os.getenv("ALERT_EMAILS", "").split(",")
        )
        alert_manager.add_notification_channel(email_channel)

    if os.getenv("WEBHOOK_URL"):
        from agents.monitoring import WebhookNotificationChannel
        webhook_channel = WebhookNotificationChannel(os.getenv("WEBHOOK_URL"))
        alert_manager.add_notification_channel(webhook_channel)

    logger.info("API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API")

    try:
        await db_pool.close()
    except Exception as exc:
        logger.error("Error while closing database pool: %s", exc, exc_info=True)

    global cache_scheduler
    if cache_scheduler is not None:
        try:
            cache_scheduler.shutdown(wait=False)
            logger.info("Cache cleanup scheduler stopped")
        except Exception as exc:
            logger.error("Error while stopping cache scheduler: %s", exc, exc_info=True)
        finally:
            cache_scheduler = None

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
