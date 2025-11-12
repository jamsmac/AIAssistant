"""
AI Assistant Platform v3.0 - Main Entry Point
Slim FastAPI application with modular architecture
"""
import os
import logging
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        release=os.getenv("RELEASE_VERSION", "3.0.0")
    )
    logger.info("Sentry initialized successfully")

# Create FastAPI application
app = FastAPI(
    title="AI Assistant Platform API",
    description="Hybrid Fractal + Multi-Agent System with Plugin Registry",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Import and setup middleware
from api.middleware import setup_middleware
setup_middleware(app)

# Import and include all routers
from api.routers import (
    auth_router,
    chat_router,
    agents_router,
    workflows_router,
    financial_router,
    projects_router,
    integrations_router,
    dashboard_router,
    models_router,
    rankings_router,
    monitoring_router,
    history_router,
    users_router,
    fractal_api,
    blog_api
)

# Include routers with proper prefixes and tags
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat_router.router, prefix="/api/chat", tags=["Chat"])
app.include_router(agents_router.router, prefix="/api/agents", tags=["Agents"])
app.include_router(workflows_router.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(financial_router.router, prefix="/api/financial", tags=["Financial"])
app.include_router(projects_router.router, prefix="/api/projects", tags=["Projects"])
app.include_router(integrations_router.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(models_router.router, prefix="/api/models", tags=["Models"])
app.include_router(rankings_router.router, prefix="/api/rankings", tags=["Rankings"])
app.include_router(monitoring_router.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(history_router.router, prefix="/api/history", tags=["History"])
app.include_router(users_router.router, prefix="/api/users", tags=["Users"])
app.include_router(fractal_api.router, prefix="/api/fractal", tags=["Fractal Agents"])
app.include_router(blog_api.router, prefix="/api/blog", tags=["Blog"])

logger.info("All routers loaded successfully")

# Root endpoint
@app.get("/")
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from api.dependencies import validate_environment
    await validate_environment()
    logger.info("AI Assistant Platform v3.0 started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AI Assistant Platform v3.0 shutting down")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
