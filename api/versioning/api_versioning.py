"""
API Versioning System
Enterprise-grade API version management with backward compatibility
"""
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import Optional, Callable, Dict, Any
from functools import wraps
from datetime import datetime, timedelta
import warnings
from enum import Enum


class APIVersion(Enum):
    """Supported API versions"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"  # Future version
    LATEST = "v2"  # Current latest version
    DEFAULT = "v1"  # Default for backward compatibility


class VersionConfig:
    """API Version configuration"""

    # Version lifecycle
    VERSIONS = {
        "v1": {
            "status": "deprecated",
            "deprecated_date": "2024-01-01",
            "sunset_date": "2024-07-01",
            "min_client_version": "1.0.0",
            "features": ["basic_auth", "simple_responses"]
        },
        "v2": {
            "status": "current",
            "release_date": "2024-01-01",
            "min_client_version": "2.0.0",
            "features": ["oauth", "pagination", "filtering", "webhooks"]
        },
        "v3": {
            "status": "beta",
            "release_date": "2024-04-01",
            "min_client_version": "3.0.0",
            "features": ["graphql", "websockets", "real_time_updates"]
        }
    }

    # Deprecation warnings
    DEPRECATION_WARNINGS = {
        "v1": "API v1 is deprecated and will be removed on 2024-07-01. Please upgrade to v2."
    }


def get_api_version(
    request: Request,
    accept_version: Optional[str] = Header(None, alias="Accept-Version"),
    api_version: Optional[str] = Header(None, alias="API-Version"),
) -> str:
    """
    Determine API version from multiple sources
    Priority: Path > Header > Query > Default
    """
    # 1. Check URL path
    path_parts = request.url.path.split('/')
    if len(path_parts) > 2 and path_parts[2] in ['v1', 'v2', 'v3']:
        return path_parts[2]

    # 2. Check headers
    if accept_version:
        return accept_version
    if api_version:
        return api_version

    # 3. Check query parameters
    if 'api_version' in request.query_params:
        return request.query_params['api_version']

    # 4. Return default
    return APIVersion.DEFAULT.value


class VersionedRouter:
    """Router with version management"""

    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.deprecations: Dict[str, list] = {}

    def add_route(self, version: str, router: APIRouter):
        """Add a router for specific version"""
        self.routers[version] = router

    def get_router(self, version: str) -> APIRouter:
        """Get router for specific version"""
        if version not in self.routers:
            raise HTTPException(
                status_code=400,
                detail=f"API version {version} not supported"
            )
        return self.routers[version]

    def deprecate_endpoint(self, version: str, path: str, sunset_date: str):
        """Mark an endpoint as deprecated"""
        if version not in self.deprecations:
            self.deprecations[version] = []

        self.deprecations[version].append({
            "path": path,
            "sunset_date": sunset_date,
            "deprecated_at": datetime.utcnow().isoformat()
        })


def versioned_endpoint(versions: list):
    """Decorator for versioned endpoints"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            version = get_api_version(request)

            if version not in versions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Endpoint not available in API version {version}"
                )

            # Add version to request state
            request.state.api_version = version

            # Add deprecation warning if applicable
            if version in VersionConfig.DEPRECATION_WARNINGS:
                response = await func(request, *args, **kwargs)
                if isinstance(response, JSONResponse):
                    response.headers["Sunset"] = VersionConfig.VERSIONS[version]["sunset_date"]
                    response.headers["Deprecation"] = "true"
                    response.headers["Warning"] = VersionConfig.DEPRECATION_WARNINGS[version]
                return response

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


class APIVersionMiddleware:
    """Middleware for API versioning"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Get API version
        version = get_api_version(request)

        # Validate version
        if version not in VersionConfig.VERSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid API version",
                    "supported_versions": list(VersionConfig.VERSIONS.keys()),
                    "latest": APIVersion.LATEST.value,
                    "default": APIVersion.DEFAULT.value
                }
            )

        # Check if version is sunset
        version_info = VersionConfig.VERSIONS[version]
        if version_info["status"] == "deprecated":
            sunset_date = datetime.fromisoformat(version_info["sunset_date"])
            if datetime.utcnow() > sunset_date:
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": f"API version {version} has been sunset",
                        "sunset_date": version_info["sunset_date"],
                        "please_use": APIVersion.LATEST.value
                    }
                )

        # Add version to request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers
        response.headers["API-Version"] = version
        response.headers["X-API-Version"] = version

        # Add deprecation headers if applicable
        if version_info["status"] == "deprecated":
            response.headers["Sunset"] = version_info["sunset_date"]
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = f'</api/{APIVersion.LATEST.value}>; rel="successor-version"'

            # Add warning header
            if version in VersionConfig.DEPRECATION_WARNINGS:
                response.headers["Warning"] = f'299 - "{VersionConfig.DEPRECATION_WARNINGS[version]}"'

        return response


# Response transformers for different versions
class ResponseTransformer:
    """Transform responses based on API version"""

    @staticmethod
    def transform_user(user: Dict[str, Any], version: str) -> Dict[str, Any]:
        """Transform user object based on version"""
        if version == "v1":
            # V1: Simple format
            return {
                "id": user.get("id"),
                "email": user.get("email"),
                "created": user.get("created_at")
            }
        elif version == "v2":
            # V2: Extended format with metadata
            return {
                "data": {
                    "type": "user",
                    "id": user.get("id"),
                    "attributes": {
                        "email": user.get("email"),
                        "created_at": user.get("created_at"),
                        "updated_at": user.get("updated_at"),
                        "is_active": user.get("is_active"),
                        "email_verified": user.get("email_verified")
                    }
                },
                "meta": {
                    "version": "v2",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        else:
            return user

    @staticmethod
    def transform_error(error: Dict[str, Any], version: str) -> Dict[str, Any]:
        """Transform error response based on version"""
        if version == "v1":
            # V1: Simple error format
            return {
                "error": error.get("message", "An error occurred"),
                "code": error.get("code", "ERROR")
            }
        elif version == "v2":
            # V2: Detailed error format
            return {
                "errors": [{
                    "status": error.get("status", 500),
                    "code": error.get("code", "INTERNAL_ERROR"),
                    "title": error.get("title", "Error"),
                    "detail": error.get("message", "An error occurred"),
                    "source": error.get("source", {}),
                    "meta": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "request_id": error.get("request_id")
                    }
                }]
            }
        else:
            return error

    @staticmethod
    def transform_collection(items: list, version: str, **kwargs) -> Dict[str, Any]:
        """Transform collection response based on version"""
        if version == "v1":
            # V1: Simple array
            return {
                "items": items,
                "count": len(items)
            }
        elif version == "v2":
            # V2: With pagination and metadata
            page = kwargs.get("page", 1)
            per_page = kwargs.get("per_page", 20)
            total = kwargs.get("total", len(items))

            return {
                "data": items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page
                },
                "links": {
                    "self": f"?page={page}&per_page={per_page}",
                    "first": f"?page=1&per_page={per_page}",
                    "last": f"?page={(total + per_page - 1) // per_page}&per_page={per_page}",
                    "prev": f"?page={page-1}&per_page={per_page}" if page > 1 else None,
                    "next": f"?page={page+1}&per_page={per_page}" if page * per_page < total else None
                },
                "meta": {
                    "version": "v2",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        else:
            return {"data": items}


# Version-specific routers
def create_v1_routes() -> APIRouter:
    """Create v1 API routes"""
    router = APIRouter(prefix="/api/v1", tags=["v1"])

    @router.get("/users")
    @versioned_endpoint(["v1"])
    async def get_users_v1():
        """V1 endpoint - deprecated"""
        users = [{"id": 1, "email": "user@example.com", "created_at": "2024-01-01"}]
        return ResponseTransformer.transform_collection(users, "v1")

    return router


def create_v2_routes() -> APIRouter:
    """Create v2 API routes"""
    router = APIRouter(prefix="/api/v2", tags=["v2"])

    @router.get("/users")
    @versioned_endpoint(["v2"])
    async def get_users_v2(page: int = 1, per_page: int = 20):
        """V2 endpoint - current"""
        users = [{"id": 1, "email": "user@example.com", "created_at": "2024-01-01"}]
        return ResponseTransformer.transform_collection(
            users, "v2", page=page, per_page=per_page, total=100
        )

    return router


# Migration helpers
class VersionMigration:
    """Help users migrate between API versions"""

    @staticmethod
    def generate_migration_guide(from_version: str, to_version: str) -> Dict[str, Any]:
        """Generate migration guide between versions"""
        return {
            "from": from_version,
            "to": to_version,
            "breaking_changes": [
                {
                    "endpoint": "/api/users",
                    "change": "Response format changed to JSON:API specification",
                    "before": {"users": []},
                    "after": {"data": [], "meta": {}}
                }
            ],
            "new_features": [
                "OAuth 2.0 authentication",
                "Pagination support",
                "Filtering and sorting",
                "Webhook subscriptions"
            ],
            "deprecations": [
                {
                    "feature": "Basic authentication",
                    "replacement": "OAuth 2.0",
                    "sunset_date": "2024-07-01"
                }
            ],
            "migration_steps": [
                "Update client library to version 2.0+",
                "Replace basic auth with OAuth",
                "Update response parsing for new format",
                "Test in staging environment"
            ]
        }


# Version discovery endpoint
async def get_api_versions():
    """Endpoint to discover available API versions"""
    versions = []

    for version, info in VersionConfig.VERSIONS.items():
        versions.append({
            "version": version,
            "status": info["status"],
            "features": info["features"],
            "links": {
                "self": f"/api/{version}",
                "docs": f"/docs/{version}",
                "schema": f"/openapi/{version}.json"
            }
        })

    return {
        "versions": versions,
        "latest": APIVersion.LATEST.value,
        "default": APIVersion.DEFAULT.value
    }