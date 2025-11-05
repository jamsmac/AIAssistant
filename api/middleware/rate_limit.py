"""
Rate Limiting Middleware
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """
    Rate limiter using sliding window algorithm
    """

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_task = None

    async def initialize(self):
        """Start background cleanup task"""
        self.cleanup_task = asyncio.create_task(self.cleanup_old_requests())

    async def cleanup_old_requests(self):
        """Remove old request records periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                current_time = time.time()
                hour_ago = current_time - 3600

                for key in list(self.requests.keys()):
                    # Remove requests older than 1 hour
                    self.requests[key] = [
                        req_time for req_time in self.requests[key]
                        if req_time > hour_ago
                    ]
                    # Remove empty keys
                    if not self.requests[key]:
                        del self.requests[key]
            except Exception as e:
                print(f"Error in rate limiter cleanup: {e}")

    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get authenticated user ID
        user = getattr(request.state, "user", None)
        if user:
            return f"user:{user['id']}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0]}"

        client = request.client
        if client:
            return f"ip:{client.host}"

        return "ip:unknown"

    def check_rate_limit(self, client_id: str) -> Tuple[bool, Dict]:
        """
        Check if client has exceeded rate limit
        Returns (is_allowed, info_dict)
        """
        current_time = time.time()
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        # Get request times for this client
        request_times = self.requests[client_id]

        # Count requests in last minute and hour
        minute_requests = sum(1 for t in request_times if t > minute_ago)
        hour_requests = sum(1 for t in request_times if t > hour_ago)

        # Check limits
        if minute_requests >= self.requests_per_minute:
            return False, {
                "limit": self.requests_per_minute,
                "window": "minute",
                "retry_after": 60 - (current_time - request_times[-self.requests_per_minute])
            }

        if hour_requests >= self.requests_per_hour:
            return False, {
                "limit": self.requests_per_hour,
                "window": "hour",
                "retry_after": 3600 - (current_time - request_times[-self.requests_per_hour])
            }

        # Add current request
        request_times.append(current_time)

        return True, {
            "remaining_minute": self.requests_per_minute - minute_requests - 1,
            "remaining_hour": self.requests_per_hour - hour_requests - 1
        }

    async def __call__(self, request: Request, call_next):
        """Middleware function"""
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/api/health", "/api/metrics"]:
            return await call_next(request)

        client_id = self.get_client_id(request)
        is_allowed, info = self.check_rate_limit(client_id)

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {info['limit']} requests per {info['window']}",
                    "retry_after": int(info['retry_after'])
                },
                headers={
                    "X-RateLimit-Limit": str(info['limit']),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + info['retry_after'])),
                    "Retry-After": str(int(info['retry_after']))
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(info['remaining_minute'])
        response.headers["X-RateLimit-Remaining-Hour"] = str(info['remaining_hour'])

        return response

def setup_rate_limiting(app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
    """Setup rate limiting middleware"""
    rate_limiter = RateLimiter(requests_per_minute, requests_per_hour)
    app.add_middleware(RateLimiter, requests_per_minute=requests_per_minute, requests_per_hour=requests_per_hour)
    return rate_limiter