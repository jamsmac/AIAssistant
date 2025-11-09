"""Security audit logging utilities."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

_AUDIT_LOGGER_NAME = "security_audit"
_AUDIT_LOG_PATH = Path("logs/security_audit.log")


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(_AUDIT_LOGGER_NAME)

    if not logger.handlers:
        _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(_AUDIT_LOG_PATH, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


def log_security_event(
    event: str,
    status: str,
    user_id: Optional[int] = None,
    ip: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Write structured security events for audit trails."""
    logger = _configure_logger()
    record = {
        "event": event,
        "status": status,
        "user_id": user_id,
        "ip": ip,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    logger.info(json.dumps(record, ensure_ascii=False))
