"""
Error Handling Middleware
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """
    Global error handler middleware
    """

    def __init__(self, app):
        self.app = app
        self.setup_handlers()

    def setup_handlers(self):
        """Setup exception handlers"""

        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            """Handle HTTP exceptions"""
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "message": str(exc.detail),
                        "status_code": exc.status_code,
                        "timestamp": datetime.now().isoformat(),
                        "path": str(request.url)
                    }
                }
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            """Handle validation errors"""
            errors = []
            for error in exc.errors():
                errors.append({
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                })

            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "message": "Validation error",
                        "status_code": 422,
                        "details": errors,
                        "timestamp": datetime.now().isoformat(),
                        "path": str(request.url)
                    }
                }
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle unexpected exceptions"""
            # Log the full traceback
            logger.error(f"Unexpected error: {exc}", exc_info=True)
            traceback_str = traceback.format_exc()

            # In production, don't expose internal errors
            if self.app.debug:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": {
                            "message": str(exc),
                            "status_code": 500,
                            "type": type(exc).__name__,
                            "traceback": traceback_str.split("\n"),
                            "timestamp": datetime.now().isoformat(),
                            "path": str(request.url)
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": {
                            "message": "Internal server error",
                            "status_code": 500,
                            "timestamp": datetime.now().isoformat(),
                            "path": str(request.url)
                        }
                    }
                )

    async def __call__(self, request: Request, call_next):
        """Middleware to catch any unhandled exceptions"""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled exception in middleware: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "status_code": 500,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )

def setup_error_handlers(app):
    """Setup error handling for the application"""
    ErrorHandlerMiddleware(app)
    return app