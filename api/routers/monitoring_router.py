"""
Monitoring Router - Handles system monitoring endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import sqlite3
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.database import get_db
from agents.ai_router import AIRouter
import agents.db_pool as db_pool_module
from agents.db_pool import get_db_pool
from agents.cache_manager import get_cache_manager
from agents.monitoring import metrics_collector, alert_manager, request_monitor, system_monitor, AlertSeverity

router = APIRouter(prefix="/api", tags=["monitoring"])


def _resolve_db_pool():
    return getattr(db_pool_module, "db_pool", get_db_pool())

# Initialize services
ai_router = AIRouter()


# Response models
class StatsResponse(BaseModel):
    calls: int
    tokens: int
    cost: float
    by_model: Dict[str, Any]
    availability: Dict[str, bool]


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, Any]
    checks: Dict[str, Any]
    router_stats: Dict[str, Any]
    timestamp: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка состояния сервиса
    
    Проверяет:
    - Доступность AI моделей
    - Статистику использования
    - Общее состояние системы
    - Версию API
    - Статус базы данных
    """
    try:
        available = ai_router._get_available_models()
        stats = ai_router.get_stats()
        cache_manager = get_cache_manager()
        cache_stats = cache_manager.get_cache_stats()
        
        # Проверка доступности базы данных
        db_status = {
            "status": "healthy",
            "response_time_ms": 0,
            "detail": None,
        }
        try:
            db = get_db()
            # Простая проверка соединения через простой запрос
            start_time = time.perf_counter()
            with sqlite3.connect(db.db_path) as conn:
                conn.execute("SELECT 1").fetchone()
            db_status["response_time_ms"] = int((time.perf_counter() - start_time) * 1000)
        except Exception as e:
            db_status["status"] = "error"
            db_status["detail"] = str(e)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Database health check failed: {e}")
        
        service_checks = {
            "anthropic": available['claude'],
            "openai": available['openai'],
            "openrouter": available['openrouter'],
            "gemini": available['gemini'],
            "ollama": available['ollama'],
            "database": db_status,
            "postgres_pool": _resolve_db_pool().get_stats(),
            "cache": {
                "total_entries": cache_stats["total_entries"],
                "active_entries": cache_stats["active_entries"],
                "expired_entries": cache_stats["expired_entries"],
            },
        }

        return HealthResponse(
            status="healthy",
            services=service_checks,
            checks=service_checks,
            router_stats={
                "total_calls": stats['calls'],
                "total_cost": stats['cost'],
                "api_version": "1.0.0"
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    try:
        db = get_db()
        with sqlite3.connect(db.db_path) as conn:
            conn.execute("SELECT 1").fetchone()
        return {"status": "ready"}
    except Exception as exc:
        return {"status": "degraded", "detail": str(exc)}


@router.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe providing uptime."""
    uptime_seconds = system_monitor.get_uptime() if hasattr(system_monitor, "get_uptime") else 0.0
    return {
        "status": "started",
        "uptime": uptime_seconds,
    }


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Получить статистику использования AI моделей
    
    Возвращает:
    - Общее количество запросов
    - Использованные токены
    - Затраченные средства
    - Статистику по каждой модели
    - Доступность моделей
    """
    try:
        stats = ai_router.get_stats()
        available = ai_router._get_available_models()
        
        return StatsResponse(
            calls=stats['calls'],
            tokens=stats['tokens'],
            cost=stats['cost'],
            by_model=stats.get('by_model', {}),
            availability=available
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """
    Получить метрики системы

    Args:
    - name: Имя метрики для фильтрации
    - start_time: Начало периода (ISO format)
    - end_time: Конец периода (ISO format)

    Returns:
    - metrics: Список метрик
    - summary: Сводная статистика
    """
    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    metrics = metrics_collector.get_metrics(name, start, end)
    summary = metrics_collector.get_summary()

    return {
        "metrics": [m.to_dict() for m in metrics[-1000:]],  # Last 1000 metrics
        "summary": summary
    }


@router.get("/alerts")
async def get_alerts(
    active_only: bool = False,
    limit: int = 100
):
    """
    Получить алерты системы

    Args:
    - active_only: Показывать только активные алерты
    - limit: Максимальное количество алертов

    Returns:
    - alerts: Список алертов
    - active_count: Количество активных алертов
    """
    if active_only:
        alerts = alert_manager.get_active_alerts()
    else:
        alerts = alert_manager.get_alert_history(limit)

    return {
        "alerts": [a.to_dict() for a in alerts],
        "active_count": len(alert_manager.get_active_alerts())
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Отметить алерт как решенный

    Args:
    - alert_id: ID алерта

    Returns:
    - resolved: True если успешно
    """
    alert_manager.resolve_alert(alert_id)
    return {"resolved": True}


@router.get("/system-status")
async def get_system_status():
    """
    Получить полный статус системы

    Returns:
    - health: Статус здоровья
    - metrics: Ключевые метрики
    - alerts: Активные алерты
    - performance: Производительность
    """
    # Get system metrics
    summary = metrics_collector.get_summary()

    # Calculate average response time
    request_durations = summary.get("histograms", {}).get("http_request_duration_seconds", {})
    avg_response_time = request_durations.get("mean", 0) if request_durations else 0

    # Get active alerts
    active_alerts = alert_manager.get_active_alerts()

    # Get request statistics
    request_stats = request_monitor.get_statistics()
    cache_stats = get_cache_manager().get_cache_stats()

    return {
        "health": {
            "status": "healthy" if len(active_alerts) == 0 else "degraded",
            "active_alerts": len(active_alerts)
        },
        "metrics": {
            "total_requests": summary.get("counters", {}).get("http_requests_total", 0),
            "average_response_time": avg_response_time,
            "error_rate": summary.get("counters", {}).get("http_errors_total", 0)
        },
        "alerts": [a.to_dict() for a in active_alerts[:10]],  # Top 10 alerts
        "performance": {
            "requests_per_second": request_stats.get("requests_per_second", 0),
            "p95_response_time": request_stats.get("p95_response_time", 0),
            "p99_response_time": request_stats.get("p99_response_time", 0)
        },
        "database_pool": _resolve_db_pool().get_stats(),
        "cache": cache_stats,
    }


@router.get("/pool-stats")
async def get_pool_stats():
    """Return statistics about the PostgreSQL connection pool."""
    return _resolve_db_pool().get_stats()


@router.get("/monitoring/pool")
async def get_pool_stats_legacy():
    """Legacy compatibility endpoint for connection pool stats."""
    return _resolve_db_pool().get_stats()


@router.get("/cache/stats")
async def get_cache_stats():
    """Return cache statistics."""
    return get_cache_manager().get_cache_stats()


@router.post("/cache/cleanup")
async def cleanup_cache():
    """Trigger cache cleanup job."""
    deleted = get_cache_manager().cleanup_expired()
    return {"deleted_entries": deleted}


@router.delete("/cache")
async def clear_cache(task_type: Optional[str] = None):
    """Clear cache entries (optionally by task type)."""
    deleted = get_cache_manager().clear_cache(task_type)
    return {"deleted_entries": deleted, "task_type": task_type}

