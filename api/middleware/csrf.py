from typing import Iterable
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from agents.csrf_protection import get_csrf_protection


SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    """Strong CSRF protection for cookie-authenticated requests."""

    def __init__(self, app, allowed_origins: Iterable[str]):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.csrf = get_csrf_protection()

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()

        if method not in SAFE_METHODS:
            if request.cookies.get("auth_token"):
                if not self._origin_allowed(request):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Invalid request origin"},
                    )

                token_header = request.headers.get("x-csrf-token")
                token = self.csrf.get_token_from_header(token_header)

                if not token or not self.csrf.verify_token(token):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Missing or invalid CSRF token"},
                    )

        return await call_next(request)

    def _origin_allowed(self, request: Request) -> bool:
        origin = request.headers.get("origin")
        current_origin = f"{request.url.scheme}://{request.url.netloc}"

        if origin:
            if origin == current_origin:
                return True
            return origin in self.allowed_origins

        referer = request.headers.get("referer")
        if referer:
            parsed = urlparse(referer)
            referer_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
            if referer_origin:
                if referer_origin == current_origin:
                    return True
                return referer_origin in self.allowed_origins

        # If neither Origin nor Referer present, treat as untrusted when cookies are present
        return False
