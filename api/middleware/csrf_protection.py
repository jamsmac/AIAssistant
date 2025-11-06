"""
CSRF Protection Middleware
Full implementation with double-submit cookie pattern and SameSite cookies
"""
import secrets
import hmac
import hashlib
import time
from typing import Optional, Tuple
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF Protection using double-submit cookie pattern with signed tokens
    """

    def __init__(
        self,
        secret_key: str,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        form_field: str = "csrf_token",
        max_age: int = 3600 * 24,  # 24 hours
        secure: bool = True,
        samesite: str = "strict",
        exempt_paths: Optional[list] = None
    ):
        self.secret_key = secret_key.encode()
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.form_field = form_field
        self.max_age = max_age
        self.secure = secure
        self.samesite = samesite
        self.exempt_paths = exempt_paths or []

        # Add default exempt paths
        self.exempt_paths.extend([
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/oauth",
            "/api/auth/callback",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ])

    def generate_token(self) -> Tuple[str, str]:
        """Generate CSRF token and its signature"""
        # Generate random token
        token = secrets.token_urlsafe(32)

        # Add timestamp for token rotation
        timestamp = str(int(time.time()))
        token_with_time = f"{token}:{timestamp}"

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key,
            token_with_time.encode(),
            hashlib.sha256
        ).hexdigest()

        # Combine token and signature
        signed_token = f"{token_with_time}:{signature}"

        return token, signed_token

    def verify_token(self, cookie_token: str, submitted_token: str) -> bool:
        """Verify CSRF token"""
        try:
            # Tokens must match exactly
            if not cookie_token or not submitted_token:
                return False

            # For double-submit pattern, tokens should match
            if cookie_token != submitted_token:
                return False

            # Verify signature
            parts = cookie_token.split(':')
            if len(parts) != 3:
                return False

            token, timestamp_str, signature = parts

            # Check token age
            timestamp = int(timestamp_str)
            current_time = int(time.time())
            if current_time - timestamp > self.max_age:
                logger.warning("CSRF token expired")
                return False

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                f"{token}:{timestamp_str}".encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("CSRF token signature mismatch")
                return False

            return True

        except Exception as e:
            logger.error(f"CSRF token verification failed: {e}")
            return False

    def is_exempt(self, path: str) -> bool:
        """Check if path is exempt from CSRF protection"""
        for exempt_path in self.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request"""
        # Check header first (preferred for AJAX)
        token = request.headers.get(self.header_name)
        if token:
            return token

        # Check form data
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                # Form data will be parsed by FastAPI
                # This would need to be handled in the route
                pass
            elif "multipart/form-data" in content_type:
                # Multipart form data
                # This would need to be handled in the route
                pass

        # Check query parameters as last resort
        token = request.query_params.get(self.form_field)
        return token

    async def __call__(self, request: Request, call_next):
        """Middleware handler"""
        # Check if path is exempt
        if self.is_exempt(request.url.path):
            return await call_next(request)

        # For safe methods, just ensure token exists
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            # Check if user has CSRF cookie, if not, generate one
            cookie_token = request.cookies.get(self.cookie_name)
            if not cookie_token:
                token, signed_token = self.generate_token()
                response = await call_next(request)

                # Set CSRF cookie
                response.set_cookie(
                    key=self.cookie_name,
                    value=signed_token,
                    max_age=self.max_age,
                    secure=self.secure,
                    httponly=False,  # Must be readable by JavaScript
                    samesite=self.samesite
                )

                # Add token to response header for client
                response.headers[self.header_name] = signed_token

                return response

            return await call_next(request)

        # For unsafe methods, verify token
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            cookie_token = request.cookies.get(self.cookie_name)
            submitted_token = self.get_token_from_request(request)

            if not cookie_token:
                logger.warning(f"CSRF cookie missing for {request.url.path}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF cookie not found"}
                )

            if not submitted_token:
                logger.warning(f"CSRF token missing in request for {request.url.path}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token not provided"}
                )

            if not self.verify_token(cookie_token, submitted_token):
                logger.warning(f"CSRF token verification failed for {request.url.path}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token verification failed"}
                )

        # Token verified, continue with request
        response = await call_next(request)

        # Rotate token on successful state-changing operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"] and response.status_code < 400:
            token, signed_token = self.generate_token()
            response.set_cookie(
                key=self.cookie_name,
                value=signed_token,
                max_age=self.max_age,
                secure=self.secure,
                httponly=False,
                samesite=self.samesite
            )
            response.headers[self.header_name] = signed_token

        return response


class CSRFTokenGenerator:
    """Utility for generating and validating CSRF tokens in routes"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def generate_form_token(self, session_id: str) -> str:
        """Generate a CSRF token bound to a session"""
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}"

        signature = hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"{data}:{signature}"

    def verify_form_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Verify a form CSRF token"""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False

            token_session, timestamp_str, signature = parts

            # Verify session ID
            if token_session != session_id:
                return False

            # Check age
            timestamp = int(timestamp_str)
            if int(time.time()) - timestamp > max_age:
                return False

            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                f"{token_session}:{timestamp_str}".encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception:
            return False


def get_csrf_token(request: Request) -> Optional[str]:
    """Helper to get CSRF token from request"""
    # Check header
    token = request.headers.get("X-CSRF-Token")
    if token:
        return token

    # Check cookie
    token = request.cookies.get("csrf_token")
    return token


def verify_csrf_exempt(func):
    """Decorator to mark routes as CSRF exempt"""
    func._csrf_exempt = True
    return func