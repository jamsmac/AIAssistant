"""
Audit Middleware
Automatically logs all API requests for audit trail
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging

from .audit_logger import audit_logger, AuditEventType, AuditSeverity


logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log API requests to audit trail

    Logs:
    - All API calls
    - Authentication attempts
    - Data access
    - Errors
    - Suspicious activity
    """

    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip audit logging for health checks and static resources
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Capture request details
        start_time = time.time()
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        correlation_id = request.headers.get("x-correlation-id")

        # Process request
        response = None
        error = None

        try:
            response = await call_next(request)
            return response

        except Exception as e:
            error = e
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Determine event type based on endpoint and method
            event_type = self._determine_event_type(request, response, error)

            # Determine severity
            severity = self._determine_severity(response, error)

            # Log audit event
            if event_type:
                try:
                    await audit_logger.log_event(
                        event_type=event_type,
                        user_id=user_id,
                        user_email=user_email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        action=f"{request.method} {request.url.path}",
                        result="success" if not error and response and response.status_code < 400 else "failure",
                        severity=severity,
                        details={
                            "method": request.method,
                            "path": request.url.path,
                            "query_params": dict(request.query_params),
                            "status_code": response.status_code if response else None,
                            "duration_ms": round(duration * 1000, 2),
                            "error": str(error) if error else None
                        },
                        correlation_id=correlation_id
                    )
                except Exception as audit_error:
                    logger.error(f"Failed to log audit event: {audit_error}")

    def _determine_event_type(
        self,
        request: Request,
        response: Response,
        error: Exception
    ) -> AuditEventType:
        """Determine audit event type based on request"""
        path = request.url.path
        method = request.method

        # Authentication endpoints
        if "/auth/login" in path:
            return AuditEventType.LOGIN_SUCCESS if not error and response and response.status_code < 400 else AuditEventType.LOGIN_FAILURE
        elif "/auth/logout" in path:
            return AuditEventType.LOGOUT
        elif "/auth/register" in path:
            return AuditEventType.USER_CREATED

        # Data operations
        elif method == "GET" and not error:
            return AuditEventType.DATA_READ
        elif method == "POST" and not error:
            return AuditEventType.DATA_CREATE
        elif method in ["PUT", "PATCH"] and not error:
            return AuditEventType.DATA_UPDATE
        elif method == "DELETE" and not error:
            return AuditEventType.DATA_DELETE

        # API calls
        elif "/api/" in path:
            if error or (response and response.status_code >= 500):
                return AuditEventType.API_ERROR
            else:
                return AuditEventType.API_CALL

        return AuditEventType.API_CALL

    def _determine_severity(self, response: Response, error: Exception) -> AuditSeverity:
        """Determine severity level"""
        if error:
            return AuditSeverity.ERROR

        if response:
            if response.status_code >= 500:
                return AuditSeverity.ERROR
            elif response.status_code >= 400:
                return AuditSeverity.WARNING
            elif response.status_code >= 200:
                return AuditSeverity.INFO

        return AuditSeverity.DEBUG
