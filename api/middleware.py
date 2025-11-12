"""
Middleware Configuration for AI Assistant Platform
Centralized middleware setup for CORS, security, monitoring, etc.
"""
import os
import time
import logging
from typing import List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk

logger = logging.getLogger(__name__)

# Default allowed origins for development
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",  # Vite dev server
]


def validate_origin(origin: str) -> bool:
    """
    Validate origin against security best practices.
    
    Args:
        origin: Origin URL to validate
        
    Returns:
        True if origin is valid, False otherwise
    """
    if not origin or not isinstance(origin, str):
        return False
    
    # Check URL format
    if not (origin.startswith("http://") or origin.startswith("https://")):
        return False
    
    # In production, only allow https:// (except localhost)
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production" and origin.startswith("http://"):
        if "localhost" not in origin:
            logger.warning(f"Rejected insecure HTTP origin in production: {origin}")
            return False
    
    # Check for dangerous patterns
    dangerous_patterns = ["<", ">", "'", '"', "javascript:", "data:", "vbscript:"]
    for pattern in dangerous_patterns:
        if pattern in origin.lower():
            logger.warning(f"Rejected origin with dangerous pattern '{pattern}': {origin}")
            return False
    
    return True


def setup_cors_middleware(app: FastAPI) -> List[str]:
    """
    Configure CORS middleware with secure settings.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        List of allowed origins
    """
    # Get production domains from environment variable
    CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "")
    production_origins = []
    
    if CORS_ORIGINS_ENV:
        # Split by comma and clean whitespace
        raw_origins = [origin.strip() for origin in CORS_ORIGINS_ENV.split(",") if origin.strip()]
        
        # Validate each origin
        for origin in raw_origins:
            if validate_origin(origin):
                production_origins.append(origin)
                logger.info(f"Added CORS origin: {origin}")
            else:
                logger.warning(f"Rejected invalid CORS origin: {origin}")
    
    # Combine default and production origins
    ALLOWED_ORIGINS = DEFAULT_ORIGINS + production_origins
    
    # Log final configuration
    logger.info(f"CORS configured with {len(ALLOWED_ORIGINS)} allowed origins")
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        logger.info(f"Production origins: {production_origins}")
    
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
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    return ALLOWED_ORIGINS


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses"""
    
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
        
        # HSTS for production (uncomment when using HTTPS)
        # if os.getenv("ENVIRONMENT", "development").lower() == "production":
        #     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Middleware for adding API version to response headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-API-Version"] = "3.0.0"
        response.headers["X-API-Server"] = "AI Assistant Platform"
        return response


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring requests and performance"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            
            # Add timing header
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            # Log slow requests
            if duration > 10:  # More than 10 seconds
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {duration:.2f} seconds"
                )
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            
            # Report to Sentry if configured
            SENTRY_DSN = os.getenv("SENTRY_DSN")
            if SENTRY_DSN:
                sentry_sdk.capture_exception(e)
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}"
            )
            
            raise


def setup_middleware(app: FastAPI):
    """
    Setup all middleware for the application.
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware (must be first)
    setup_cors_middleware(app)
    logger.info("CORS middleware configured")
    
    # Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    logger.info("Gzip middleware configured")
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware configured")
    
    # API version middleware
    app.add_middleware(APIVersionMiddleware)
    logger.info("API version middleware configured")
    
    # Monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    logger.info("Monitoring middleware configured")
