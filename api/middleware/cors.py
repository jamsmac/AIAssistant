"""
CORS Middleware Configuration
"""

from fastapi.middleware.cors import CORSMiddleware
import os

# Define allowed development origins
# NEVER use ["*"] with allow_credentials=True as it violates CORS specification
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000"
]

def setup_cors(app):
    """Configure CORS for the application"""

    # Determine allowed origins based on environment
    if os.getenv("ENVIRONMENT") == "production":
        # In production, use specific domains from CORS_ORIGINS env variable
        cors_env = os.getenv("CORS_ORIGINS", "")
        allowed_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

        if not allowed_origins:
            # Fallback: use FRONTEND_URL or ALLOWED_ORIGINS
            allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
            if not allowed_origins or allowed_origins == [""]:
                # Last resort: use FRONTEND_URL
                frontend_url = os.getenv("FRONTEND_URL", "")
                if frontend_url:
                    allowed_origins = [frontend_url]
                else:
                    # Default production origins (should be overridden in production!)
                    allowed_origins = [
                        "https://aiassistant.vercel.app",
                        "https://www.aiassistant.vercel.app"
                    ]
    else:
        # In development, use specific localhost origins
        # NEVER use ["*"] with allow_credentials=True
        allowed_origins = DEV_ORIGINS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
        expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
    )

    return app