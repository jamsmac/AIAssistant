"""
Centralized Logging System
Enterprise-grade structured logging with multiple backends
"""
import os
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
import traceback
from functools import wraps
import asyncio
import httpx

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # json or text
ENABLE_SENTRY = os.getenv('SENTRY_DSN', '') != ''
ENABLE_LOGSTASH = os.getenv('LOGSTASH_HOST', '') != ''
ENABLE_CLOUDWATCH = os.getenv('AWS_REGION', '') != ''


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all logs for request tracing"""

    def filter(self, record):
        import contextvars
        correlation_id = getattr(contextvars, 'correlation_id', None)
        record.correlation_id = correlation_id.get() if correlation_id else 'none'
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Enhanced JSON formatter with additional fields"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Add environment info
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['service'] = 'aiassistant-api'
        log_record['version'] = os.getenv('APP_VERSION', 'unknown')
        log_record['host'] = os.getenv('HOSTNAME', 'unknown')

        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id

        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            log_record['stack_trace'] = traceback.format_tb(record.exc_info[2])


class LogstashHandler(logging.Handler):
    """Send logs to Logstash via TCP"""

    def __init__(self, host: str, port: int = 5000):
        super().__init__()
        self.host = host
        self.port = port
        self.client = None

    async def emit_async(self, record):
        """Async log emission to Logstash"""
        try:
            if not self.client:
                self.client = httpx.AsyncClient()

            log_entry = {
                '@timestamp': datetime.utcnow().isoformat(),
                '@version': '1',
                'message': self.format(record),
                'host': self.host,
                'level': record.levelname,
                'logger': record.name,
                'thread': record.thread,
                'path': record.pathname,
                'line': record.lineno,
                'function': record.funcName
            }

            await self.client.post(
                f'http://{self.host}:{self.port}',
                json=log_entry,
                timeout=1.0
            )
        except Exception:
            self.handleError(record)

    def emit(self, record):
        """Sync wrapper for async emission"""
        try:
            asyncio.create_task(self.emit_async(record))
        except RuntimeError:
            # Not in async context, skip
            pass


class CloudWatchHandler(logging.Handler):
    """Send logs to AWS CloudWatch"""

    def __init__(self, log_group: str, log_stream: str):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream

        try:
            import boto3
            self.client = boto3.client('logs', region_name=os.getenv('AWS_REGION'))
            self.sequence_token = None
        except ImportError:
            self.client = None

    def emit(self, record):
        """Send log to CloudWatch"""
        if not self.client:
            return

        try:
            log_event = {
                'timestamp': int(record.created * 1000),
                'message': json.dumps({
                    'level': record.levelname,
                    'message': self.format(record),
                    'logger': record.name,
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                })
            }

            kwargs = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [log_event]
            }

            if self.sequence_token:
                kwargs['sequenceToken'] = self.sequence_token

            response = self.client.put_log_events(**kwargs)
            self.sequence_token = response.get('nextSequenceToken')

        except Exception:
            self.handleError(record)


class StructuredLogger:
    """Main logger class with structured logging support"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_handlers()

    def setup_handlers(self):
        """Configure all logging handlers"""
        self.logger.setLevel(getattr(logging, LOG_LEVEL))

        # Remove existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)

        if LOG_FORMAT == 'json':
            formatter = CustomJsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Add correlation ID filter
        self.logger.addFilter(CorrelationIdFilter())

        # Logstash handler
        if ENABLE_LOGSTASH:
            logstash_handler = LogstashHandler(
                host=os.getenv('LOGSTASH_HOST'),
                port=int(os.getenv('LOGSTASH_PORT', 5000))
            )
            logstash_handler.setFormatter(CustomJsonFormatter())
            self.logger.addHandler(logstash_handler)

        # CloudWatch handler
        if ENABLE_CLOUDWATCH:
            cloudwatch_handler = CloudWatchHandler(
                log_group=os.getenv('CLOUDWATCH_LOG_GROUP', 'aiassistant'),
                log_stream=os.getenv('CLOUDWATCH_LOG_STREAM', 'api')
            )
            cloudwatch_handler.setFormatter(CustomJsonFormatter())
            self.logger.addHandler(cloudwatch_handler)

        # Sentry integration
        if ENABLE_SENTRY:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.logging import LoggingIntegration

                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )

                sentry_sdk.init(
                    dsn=os.getenv('SENTRY_DSN'),
                    integrations=[sentry_logging],
                    environment=os.getenv('ENVIRONMENT', 'development'),
                    traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1))
                )
            except ImportError:
                pass

    def log_event(self, level: str, event: str, **kwargs):
        """Log a structured event"""
        log_data = {
            'event': event,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }

        getattr(self.logger, level.lower())(json.dumps(log_data))

    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        if kwargs:
            self.logger.info(message, extra={'data': kwargs})
        else:
            self.logger.info(message)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error with exception details"""
        extra = {'data': kwargs}

        if exception:
            extra['exception_type'] = type(exception).__name__
            extra['exception_message'] = str(exception)
            extra['stack_trace'] = traceback.format_exc()

        self.logger.error(message, extra=extra, exc_info=exception)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if kwargs:
            self.logger.warning(message, extra={'data': kwargs})
        else:
            self.logger.warning(message)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if kwargs:
            self.logger.debug(message, extra={'data': kwargs})
        else:
            self.logger.debug(message)

    def audit(self, action: str, user_id: Optional[int] = None, **kwargs):
        """Log audit event"""
        self.log_event(
            'info',
            'audit',
            action=action,
            user_id=user_id,
            **kwargs
        )

    def metric(self, name: str, value: float, unit: str = 'count', **tags):
        """Log metric data"""
        self.log_event(
            'info',
            'metric',
            metric_name=name,
            value=value,
            unit=unit,
            tags=tags
        )


def get_logger(name: str) -> StructuredLogger:
    """Factory function to get a configured logger"""
    return StructuredLogger(name)


# Decorators for automatic logging
def log_function_call(logger: StructuredLogger):
    """Decorator to log function calls"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.debug(f"Calling {func.__name__}", args=args, kwargs=kwargs)

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.info(
                    f"Function {func.__name__} completed",
                    duration=duration,
                    success=True
                )
                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.error(
                    f"Function {func.__name__} failed",
                    exception=e,
                    duration=duration,
                    success=False
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            logger.debug(f"Calling {func.__name__}", args=args, kwargs=kwargs)

            try:
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.info(
                    f"Function {func.__name__} completed",
                    duration=duration,
                    success=True
                )
                return result

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.error(
                    f"Function {func.__name__} failed",
                    exception=e,
                    duration=duration,
                    success=False
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def log_api_request(logger: StructuredLogger):
    """Decorator for API endpoint logging"""

    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            start_time = datetime.utcnow()

            # Log request
            logger.info(
                "API Request",
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                client_host=request.client.host if request.client else None
            )

            try:
                response = await func(request, *args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()

                # Log response
                logger.info(
                    "API Response",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code if hasattr(response, 'status_code') else 200,
                    duration=duration
                )

                return response

            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()

                logger.error(
                    "API Error",
                    method=request.method,
                    path=request.url.path,
                    exception=e,
                    duration=duration
                )
                raise

        return wrapper

    return decorator


# Global logger instance
logger = get_logger(__name__)