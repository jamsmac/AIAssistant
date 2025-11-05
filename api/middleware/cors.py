"""
CORS Middleware Configuration
"""

from fastapi.middleware.cors import CORSMiddleware
import os

def setup_cors(app):
    """Configure CORS for the application"""

    # Determine allowed origins based on environment
    if os.getenv("ENVIRONMENT") == "production":
        # In production, use specific domains
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        if not allowed_origins or allowed_origins == [""]:
            # Default production origins
            allowed_origins = [
                "https://aiassistant.vercel.app",
                "https://www.aiassistant.vercel.app",
                os.getenv("FRONTEND_URL", "https://localhost:3000")
            ]
    else:
        # In development, allow all origins
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
    )

    return app