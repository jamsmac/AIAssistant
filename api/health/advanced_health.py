"""
Advanced Health Check System
Enterprise-grade health monitoring with detailed diagnostics
"""
import os
import time
import psutil
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import json
import asyncpg
import redis
from fastapi import APIRouter, Response, status
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class HealthComponent(Enum):
    """System components to check"""
    DATABASE = "database"
    REDIS = "redis"
    EXTERNAL_APIS = "external_apis"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    SERVICES = "services"


class HealthChecker:
    """Comprehensive health checking system"""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.check_results: Dict[str, Any] = {}
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "response_time_ms": 1000,
            "error_rate_percent": 5
        }

    async def check_database(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check database connectivity and performance"""
        details = {
            "type": os.getenv("DB_TYPE", "sqlite"),
            "status": HealthStatus.UNHEALTHY.value,
            "response_time_ms": None,
            "connection_pool": {},
            "checks": []
        }

        start_time = time.time()

        try:
            if os.getenv("DATABASE_URL"):
                # PostgreSQL check
                conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

                # Basic connectivity
                version = await conn.fetchval("SELECT version()")
                details["version"] = version.split(",")[0]

                # Performance check
                await conn.fetchval("SELECT 1")
                response_time = (time.time() - start_time) * 1000
                details["response_time_ms"] = round(response_time, 2)

                # Connection pool stats
                pool_stats = await conn.fetchrow("""
                    SELECT count(*) as total,
                           count(*) FILTER (WHERE state = 'active') as active,
                           count(*) FILTER (WHERE state = 'idle') as idle
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
                details["connection_pool"] = dict(pool_stats) if pool_stats else {}

                # Table checks
                table_count = await conn.fetchval("""
                    SELECT count(*) FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                details["table_count"] = table_count

                await conn.close()

                # Determine status
                if response_time < 100:
                    details["status"] = HealthStatus.HEALTHY.value
                elif response_time < 500:
                    details["status"] = HealthStatus.DEGRADED.value
                else:
                    details["status"] = HealthStatus.UNHEALTHY.value

                return HealthStatus[details["status"].upper()], details

            else:
                # SQLite check
                import sqlite3
                conn = sqlite3.connect("./data/production.db")
                cursor = conn.cursor()

                cursor.execute("SELECT sqlite_version()")
                details["version"] = f"SQLite {cursor.fetchone()[0]}"

                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                details["table_count"] = cursor.fetchone()[0]

                response_time = (time.time() - start_time) * 1000
                details["response_time_ms"] = round(response_time, 2)

                conn.close()

                details["status"] = HealthStatus.HEALTHY.value
                return HealthStatus.HEALTHY, details

        except Exception as e:
            details["error"] = str(e)
            details["status"] = HealthStatus.CRITICAL.value
            logger.error(f"Database health check failed: {e}")
            return HealthStatus.CRITICAL, details

    async def check_redis(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check Redis connectivity if configured"""
        details = {
            "status": HealthStatus.UNHEALTHY.value,
            "connected": False,
            "response_time_ms": None
        }

        if not os.getenv("REDIS_URL"):
            details["status"] = "not_configured"
            return HealthStatus.HEALTHY, details

        try:
            import redis.asyncio as aioredis
            start_time = time.time()

            r = await aioredis.from_url(os.getenv("REDIS_URL"))
            await r.ping()

            # Get info
            info = await r.info()
            details["version"] = info.get("redis_version", "unknown")
            details["connected_clients"] = info.get("connected_clients", 0)
            details["used_memory_human"] = info.get("used_memory_human", "unknown")
            details["uptime_in_days"] = info.get("uptime_in_days", 0)

            response_time = (time.time() - start_time) * 1000
            details["response_time_ms"] = round(response_time, 2)

            await r.close()

            details["connected"] = True
            details["status"] = HealthStatus.HEALTHY.value
            return HealthStatus.HEALTHY, details

        except Exception as e:
            details["error"] = str(e)
            details["status"] = HealthStatus.UNHEALTHY.value
            return HealthStatus.UNHEALTHY, details

    async def check_external_apis(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check external API connectivity"""
        apis = {
            "openai": {
                "url": "https://api.openai.com/v1/models",
                "headers": {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"},
                "timeout": 5
            },
            "anthropic": {
                "url": "https://api.anthropic.com/v1/messages",
                "headers": {"x-api-key": os.getenv("ANTHROPIC_API_KEY", "")},
                "timeout": 5
            }
        }

        results = {}
        overall_status = HealthStatus.HEALTHY

        async with httpx.AsyncClient() as client:
            for api_name, config in apis.items():
                start_time = time.time()
                try:
                    if config["headers"].get("Authorization") == "Bearer " or \
                       config["headers"].get("x-api-key") == "":
                        results[api_name] = {
                            "status": "not_configured",
                            "response_time_ms": None
                        }
                        continue

                    response = await client.get(
                        config["url"],
                        headers=config["headers"],
                        timeout=config["timeout"]
                    )

                    response_time = (time.time() - start_time) * 1000

                    results[api_name] = {
                        "status": "healthy" if response.status_code < 500 else "unhealthy",
                        "status_code": response.status_code,
                        "response_time_ms": round(response_time, 2)
                    }

                    if response.status_code >= 500:
                        overall_status = HealthStatus.DEGRADED

                except Exception as e:
                    results[api_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "response_time_ms": None
                    }
                    overall_status = HealthStatus.DEGRADED

        return overall_status, {"apis": results, "status": overall_status.value}

    async def check_system_resources(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory usage
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk usage
            disk = psutil.disk_usage('/')

            # Network I/O
            network = psutil.net_io_counters()

            # Process info
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "threads": process.num_threads(),
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "cpu_percent": process.cpu_percent()
            }

            resources = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "status": self._get_resource_status(cpu_percent, self.thresholds["cpu_percent"])
                },
                "memory": {
                    "percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                    "status": self._get_resource_status(memory.percent, self.thresholds["memory_percent"])
                },
                "swap": {
                    "percent": swap.percent,
                    "used_gb": round(swap.used / (1024**3), 2),
                    "total_gb": round(swap.total / (1024**3), 2)
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": round(disk.free / (1024**3), 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "status": self._get_resource_status(disk.percent, self.thresholds["disk_percent"])
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": process_info
            }

            # Determine overall status
            statuses = [
                resources["cpu"]["status"],
                resources["memory"]["status"],
                resources["disk"]["status"]
            ]

            if any(s == "critical" for s in statuses):
                overall_status = HealthStatus.CRITICAL
            elif any(s == "unhealthy" for s in statuses):
                overall_status = HealthStatus.UNHEALTHY
            elif any(s == "degraded" for s in statuses):
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.HEALTHY

            return overall_status, resources

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return HealthStatus.UNHEALTHY, {"error": str(e)}

    def _get_resource_status(self, current: float, threshold: float) -> str:
        """Determine resource status based on threshold"""
        if current < threshold * 0.7:
            return "healthy"
        elif current < threshold * 0.9:
            return "degraded"
        elif current < threshold:
            return "unhealthy"
        else:
            return "critical"

    async def check_dependencies(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """Check critical dependencies"""
        dependencies = {
            "python_version": {
                "required": "3.11",
                "current": f"{os.sys.version_info.major}.{os.sys.version_info.minor}"
            },
            "required_modules": {}
        }

        # Check required Python packages
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "asyncpg",
            "redis", "httpx", "prometheus_client"
        ]

        for package in required_packages:
            try:
                module = __import__(package)
                version = getattr(module, "__version__", "unknown")
                dependencies["required_modules"][package] = {
                    "installed": True,
                    "version": version
                }
            except ImportError:
                dependencies["required_modules"][package] = {
                    "installed": False,
                    "version": None
                }

        # Check if all required modules are installed
        all_installed = all(
            info["installed"]
            for info in dependencies["required_modules"].values()
        )

        status = HealthStatus.HEALTHY if all_installed else HealthStatus.UNHEALTHY

        return status, dependencies

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_report = {
            "status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": str(datetime.utcnow() - self.start_time),
            "version": os.getenv("APP_VERSION", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "checks": {}
        }

        # Run all checks concurrently
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_external_apis(),
            self.check_system_resources(),
            self.check_dependencies(),
            return_exceptions=True
        )

        # Process results
        check_names = ["database", "redis", "external_apis", "system_resources", "dependencies"]
        statuses = []

        for name, result in zip(check_names, checks):
            if isinstance(result, Exception):
                health_report["checks"][name] = {
                    "status": HealthStatus.CRITICAL.value,
                    "error": str(result)
                }
                statuses.append(HealthStatus.CRITICAL)
            else:
                status, details = result
                health_report["checks"][name] = details
                statuses.append(status)

        # Determine overall status
        if HealthStatus.CRITICAL in statuses:
            health_report["status"] = HealthStatus.CRITICAL.value
        elif HealthStatus.UNHEALTHY in statuses:
            health_report["status"] = HealthStatus.UNHEALTHY.value
        elif HealthStatus.DEGRADED in statuses:
            health_report["status"] = HealthStatus.DEGRADED.value
        else:
            health_report["status"] = HealthStatus.HEALTHY.value

        # Add SLA information
        health_report["sla"] = {
            "target": "99.9%",
            "current_month": self._calculate_sla(),
            "incidents_today": 0
        }

        return health_report

    def _calculate_sla(self) -> str:
        """Calculate current SLA percentage"""
        # This would normally query from monitoring system
        # For now, return mock value
        return "99.95%"


# FastAPI router for health endpoints
router = APIRouter(prefix="/health", tags=["health"])

# Global health checker instance
health_checker = HealthChecker()


@router.get("/")
async def health_check(response: Response):
    """Basic health check endpoint"""
    try:
        health = await health_checker.get_comprehensive_health()

        # Set appropriate status code
        if health["status"] == HealthStatus.CRITICAL.value:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health["status"] == HealthStatus.UNHEALTHY.value:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health["status"] == HealthStatus.DEGRADED.value:
            response.status_code = status.HTTP_200_OK  # Still operational
        else:
            response.status_code = status.HTTP_200_OK

        return health

    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": HealthStatus.CRITICAL.value,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_check(response: Response):
    """Kubernetes readiness probe endpoint"""
    # Quick check of critical components only
    try:
        db_status, _ = await health_checker.check_database()

        if db_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
            return {"status": "ready"}
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "not_ready"}

    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}


@router.get("/startup")
async def startup_check():
    """Kubernetes startup probe endpoint"""
    return {
        "status": "started",
        "uptime": str(datetime.utcnow() - health_checker.start_time)
    }