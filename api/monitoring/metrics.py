"""
Production Monitoring and Metrics
Enterprise-grade observability
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

active_users_gauge = Gauge(
    'active_users',
    'Number of active users'
)

database_connections_gauge = Gauge(
    'database_connections',
    'Number of active database connections'
)

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI model requests',
    ['provider', 'model', 'status']
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI model request latency',
    ['provider', 'model']
)

ai_tokens_used_total = Counter(
    'ai_tokens_used_total',
    'Total tokens used',
    ['provider', 'model']
)

error_rate_gauge = Gauge(
    'error_rate',
    'Current error rate percentage'
)

# Business metrics
registered_users_total = Counter(
    'registered_users_total',
    'Total registered users'
)

projects_created_total = Counter(
    'projects_created_total',
    'Total projects created'
)

workflows_executed_total = Counter(
    'workflows_executed_total',
    'Total workflows executed',
    ['status']
)

revenue_gauge = Gauge(
    'revenue_total_usd',
    'Total revenue in USD'
)


class MetricsMiddleware:
    """Middleware to collect metrics"""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()

    async def __call__(self, request: Request, call_next):
        # Start timing
        start_time = time.time()

        # Process request
        try:
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            # Track errors
            if response.status_code >= 400:
                self.error_count += 1

            self.request_count += 1

            # Calculate error rate
            if self.request_count > 0:
                error_rate = (self.error_count / self.request_count) * 100
                error_rate_gauge.set(error_rate)

            return response

        except Exception as e:
            # Log error
            logger.error(f"Request failed: {e}")
            self.error_count += 1
            raise


class SystemMetrics:
    """System-level metrics collector"""

    @staticmethod
    def collect():
        """Collect system metrics"""
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "network_io": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            },
            "process": {
                "threads": psutil.Process().num_threads(),
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent()
            }
        }
        return metrics


class AIMetrics:
    """AI model usage metrics"""

    @staticmethod
    def record_request(provider: str, model: str, tokens: int, duration: float, success: bool):
        """Record AI model request metrics"""
        status = "success" if success else "failure"

        ai_requests_total.labels(
            provider=provider,
            model=model,
            status=status
        ).inc()

        if success:
            ai_request_duration_seconds.labels(
                provider=provider,
                model=model
            ).observe(duration)

            ai_tokens_used_total.labels(
                provider=provider,
                model=model
            ).inc(tokens)


class BusinessMetrics:
    """Business-level metrics"""

    @staticmethod
    def record_user_registration():
        """Record new user registration"""
        registered_users_total.inc()

    @staticmethod
    def record_project_creation():
        """Record project creation"""
        projects_created_total.inc()

    @staticmethod
    def record_workflow_execution(status: str):
        """Record workflow execution"""
        workflows_executed_total.labels(status=status).inc()

    @staticmethod
    def update_revenue(amount: float):
        """Update revenue metric"""
        revenue_gauge.set(amount)


async def get_health_metrics() -> Dict[str, Any]:
    """Get comprehensive health metrics"""
    system_metrics = SystemMetrics.collect()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy" if system_metrics["cpu_percent"] < 80 else "degraded",
        "system": system_metrics,
        "application": {
            "uptime_seconds": (datetime.utcnow() - datetime.utcnow()).total_seconds(),
            "active_users": active_users_gauge._value.get(),
            "database_connections": database_connections_gauge._value.get(),
            "error_rate": error_rate_gauge._value.get()
        },
        "business": {
            "total_users": registered_users_total._value.get(),
            "total_projects": projects_created_total._value.get(),
            "total_workflows": workflows_executed_total._value.get()
        }
    }


async def prometheus_metrics(request: Request) -> Response:
    """Endpoint for Prometheus to scrape metrics"""
    metrics = generate_latest()
    return Response(content=metrics, media_type="text/plain")


# Alerting rules (for Prometheus)
ALERT_RULES = """
groups:
- name: aiassistant_alerts
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: error_rate > 5
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      description: "Error rate is {{ $value }}%"

  - alert: HighCPUUsage
    expr: process_cpu_seconds_total > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High CPU usage
      description: "CPU usage is {{ $value }}%"

  - alert: HighMemoryUsage
    expr: process_resident_memory_bytes / 1024 / 1024 > 1024
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High memory usage
      description: "Memory usage is {{ $value }}MB"

  - alert: DatabaseConnectionPoolExhausted
    expr: database_connections >= 18
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Database connection pool almost exhausted
      description: "{{ $value }} of 20 connections in use"

  - alert: HighAIApiLatency
    expr: histogram_quantile(0.95, ai_request_duration_seconds) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High AI API latency
      description: "95th percentile latency is {{ $value }}s"
"""