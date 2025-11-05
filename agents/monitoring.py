"""
Monitoring and Alerting System
Tracks system metrics, errors, and performance
"""

import time
import json
import logging
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Metric:
    """Metric data point"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None

    def to_dict(self):
        data = asdict(self)
        data['type'] = self.type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class Alert:
    """Alert notification"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self):
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data

class MetricsCollector:
    """Collect and store metrics"""

    def __init__(self, max_history: int = 10000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

    def increment_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] += value

        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self.counters[key],
            timestamp=datetime.utcnow(),
            labels=labels
        )
        self.metrics[key].append(metric)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value

        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels
        )
        self.metrics[key].append(metric)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

        # Keep only last 1000 values for histogram
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]

        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels
        )
        self.metrics[key].append(metric)

    def get_metrics(self, name: str = None, start_time: datetime = None, end_time: datetime = None) -> List[Metric]:
        """Get metrics by name and time range"""
        results = []

        for key, metrics_deque in self.metrics.items():
            if name and not key.startswith(name):
                continue

            for metric in metrics_deque:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                results.append(metric)

        return sorted(results, key=lambda x: x.timestamp)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            "counters": {k: v for k, v in self.counters.items()},
            "gauges": {k: v for k, v in self.gauges.items()},
            "histograms": {}
        }

        # Calculate histogram statistics
        for key, values in self.histograms.items():
            if values:
                sorted_values = sorted(values)
                summary["histograms"][key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "p50": sorted_values[len(sorted_values) // 2],
                    "p95": sorted_values[int(len(sorted_values) * 0.95)],
                    "p99": sorted_values[int(len(sorted_values) * 0.99)]
                }

        return summary

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create a unique key for metric"""
        if not labels:
            return name
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

class AlertManager:
    """Manage alerts and notifications"""

    def __init__(self, db=None):
        self.db = db
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.notification_channels = []

        if db:
            self._ensure_tables()

    def _ensure_tables(self):
        """Create alert tables if needed"""
        if self.db:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP
                )
            """)

    def create_alert(self,
                    severity: AlertSeverity,
                    title: str,
                    message: str,
                    source: str,
                    metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        import uuid

        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            source=source,
            metadata=metadata
        )

        self.alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Store in database if available
        if self.db:
            self.db.execute_query(
                """
                INSERT INTO alerts (id, severity, title, message, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (alert_id, severity.value, title, message, source,
                 json.dumps(metadata) if metadata else None)
            )

        # Send notifications
        asyncio.create_task(self._send_notifications(alert))

        return alert

    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()

            if self.db:
                self.db.execute_query(
                    """
                    UPDATE alerts
                    SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (alert_id,)
                )

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        for channel in self.notification_channels:
            try:
                await channel.send(alert)
            except Exception as e:
                logger.error(f"Failed to send alert through {channel.__class__.__name__}: {e}")

    def add_notification_channel(self, channel):
        """Add a notification channel"""
        self.notification_channels.append(channel)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]

class SystemMonitor:
    """Monitor system resources"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.running = False

    async def start(self, interval: int = 60):
        """Start monitoring system resources"""
        self.running = True

        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.set_gauge("system_cpu_percent", cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.set_gauge("system_memory_percent", memory.percent)
                self.metrics.set_gauge("system_memory_available_bytes", memory.available)

                # Disk usage
                disk = psutil.disk_usage('/')
                self.metrics.set_gauge("system_disk_percent", disk.percent)
                self.metrics.set_gauge("system_disk_free_bytes", disk.free)

                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics.set_gauge("system_network_bytes_sent", net_io.bytes_sent)
                self.metrics.set_gauge("system_network_bytes_recv", net_io.bytes_recv)

                # Process count
                process_count = len(psutil.pids())
                self.metrics.set_gauge("system_process_count", process_count)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            await asyncio.sleep(interval)

    def stop(self):
        """Stop monitoring"""
        self.running = False

class RequestMonitor:
    """Monitor HTTP requests"""

    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager):
        self.metrics = metrics_collector
        self.alerts = alert_manager

    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        labels = {
            "method": method,
            "path": path,
            "status": str(status_code)
        }

        # Count requests
        self.metrics.increment_counter("http_requests_total", labels=labels)

        # Record duration
        self.metrics.record_histogram("http_request_duration_seconds", duration, labels=labels)

        # Count errors
        if status_code >= 500:
            self.metrics.increment_counter("http_errors_total", labels={"type": "5xx"})

            # Alert on high error rate
            error_count = self.metrics.counters.get("http_errors_total{type=5xx}", 0)
            if error_count > 100:  # More than 100 5xx errors
                self.alerts.create_alert(
                    severity=AlertSeverity.WARNING,
                    title="High 5xx Error Rate",
                    message=f"Detected {error_count} 5xx errors",
                    source="RequestMonitor",
                    metadata={"path": path, "status_code": status_code}
                )
        elif status_code >= 400:
            self.metrics.increment_counter("http_errors_total", labels={"type": "4xx"})

class EmailNotificationChannel:
    """Send alerts via email"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to_emails = to_emails

    async def send(self, alert: Alert):
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            body = f"""
Alert Details:
--------------
Severity: {alert.severity.value}
Source: {alert.source}
Time: {alert.timestamp.isoformat()}

Message:
{alert.message}

Metadata:
{json.dumps(alert.metadata, indent=2) if alert.metadata else 'None'}
"""

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

class WebhookNotificationChannel:
    """Send alerts via webhook"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, alert: Alert):
        """Send alert via webhook"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.webhook_url,
                    json=alert.to_dict(),
                    timeout=10
                )
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

# Global instances
metrics_collector = MetricsCollector()
alert_manager = AlertManager()
request_monitor = RequestMonitor(metrics_collector, alert_manager)
system_monitor = SystemMonitor(metrics_collector)