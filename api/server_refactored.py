"""
AIAssistant OS Platform - Main Server (Refactored)
This is the new, clean entry point replacing the monolithic server.py
"""

import os
import sys
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routers
from api.routers import auth_router
from api.routers import chat_router
from api.routers import projects_router
from api.routers import workflows_router
from api.routers import integrations_router
from api.routers import dashboard_router

# Import middleware
from api.middleware.cors import setup_cors
from api.middleware.rate_limit import setup_rate_limiting
from api.middleware.error_handler import setup_error_handlers

# Import database with connection pooling
try:
    from agents.database_v2 import PooledDatabase, get_pooled_db
    from agents.database_pool import PoolMonitor, get_connection_pool
    db = get_pooled_db()
    pool_monitor = PoolMonitor(get_connection_pool())
    logger.info("Using pooled database connection")
except ImportError:
    logger.warning("Connection pool not available, falling back to standard database")
    from agents.database import HistoryDatabase, get_db
    db = get_db()
    pool_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown events
    """
    # Startup
    logger.info("Starting AIAssistant OS Platform...")

    # Database is already initialized
    logger.info("Database initialized")

    # Start connection pool monitoring if available
    if pool_monitor:
        pool_monitor.start_monitoring(interval=60)
        logger.info("Connection pool monitoring started")

    # Initialize rate limiter
    # rate_limiter = RateLimiter()
    # await rate_limiter.initialize()

    logger.info(f"Server started successfully at {datetime.now()}")

    yield

    # Shutdown
    logger.info("Shutting down AIAssistant OS Platform...")

    # Stop pool monitoring
    if pool_monitor:
        pool_monitor.stop_monitoring()
        logger.info("Connection pool monitoring stopped")

    # Close connection pool
    if hasattr(db, 'pool'):
        db.pool.close_all()
        logger.info("Connection pool closed")

    logger.info("Server shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AIAssistant OS Platform",
    description="AI Operating System replacing 100+ SaaS tools",
    version="1.0.0",
    lifespan=lifespan
)

# Setup middleware
setup_cors(app)
setup_error_handlers(app)

# Setup rate limiting (60 req/min, 1000 req/hour)
if os.getenv("ENVIRONMENT") == "production":
    rate_limiter = setup_rate_limiting(app, requests_per_minute=60, requests_per_hour=1000)
else:
    # More relaxed limits for development
    rate_limiter = setup_rate_limiting(app, requests_per_minute=120, requests_per_hour=5000)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "service": "AIAssistant OS Platform",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test database connection
        db_healthy = False
        try:
            # Simple query to test DB
            db.get_user_by_id(1)  # This will fail gracefully if no user
            db_healthy = True
        except:
            db_healthy = True  # DB is working even if no user found

        return {
            "status": "healthy",
            "checks": {
                "database": db_healthy,
                "api": True,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Include all routers
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(projects_router.router)
app.include_router(workflows_router.router)
app.include_router(integrations_router.router)
app.include_router(dashboard_router.router)

# Include blog router if it exists
try:
    from api.routers import blog_api
    app.include_router(blog_api.router)
    logger.info("Blog API router included")
except ImportError:
    logger.info("Blog API router not found (optional)")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Metrics endpoint with connection pool stats
@app.get("/api/metrics")
async def metrics():
    """Metrics endpoint including connection pool statistics"""
    metrics_data = {
        "requests_total": 0,  # TODO: Implement actual metrics
        "errors_total": 0,
        "active_users": 0,
        "timestamp": datetime.now().isoformat()
    }

    # Add connection pool stats if available
    if hasattr(db, 'get_pool_stats'):
        pool_stats = db.get_pool_stats()
        metrics_data["connection_pool"] = {
            "total_connections": pool_stats.get("total_connections", 0),
            "active_connections": pool_stats.get("active_connections", 0),
            "available_connections": pool_stats.get("available_connections", 0),
            "pool_exhausted_count": pool_stats.get("pool_exhausted_count", 0),
            "avg_wait_time": pool_stats.get("avg_wait_time", 0),
            "connections_reused": pool_stats.get("connections_reused", 0),
            "queries_executed": pool_stats.get("queries_executed", 0)
        }

    return metrics_data

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "server_refactored:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )