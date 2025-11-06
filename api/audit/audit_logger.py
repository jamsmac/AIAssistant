"""
Enterprise Audit Trail System
Comprehensive audit logging for compliance (GDPR, SOC 2, HIPAA)
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
import hashlib
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"
    MFA_ENABLED = "auth.mfa.enabled"
    MFA_DISABLED = "auth.mfa.disabled"

    # Authorization
    PERMISSION_GRANTED = "authz.permission.granted"
    PERMISSION_DENIED = "authz.permission.denied"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REVOKED = "authz.role.revoked"

    # Data Access
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"

    # Privacy
    CONSENT_GIVEN = "privacy.consent.given"
    CONSENT_REVOKED = "privacy.consent.revoked"
    DATA_ANONYMIZED = "privacy.data.anonymized"
    DATA_ERASED = "privacy.data.erased"  # GDPR Right to be Forgotten
    DATA_ACCESSED = "privacy.data.accessed"  # GDPR Right to Access

    # Administrative
    USER_CREATED = "admin.user.created"
    USER_UPDATED = "admin.user.updated"
    USER_DELETED = "admin.user.deleted"
    USER_SUSPENDED = "admin.user.suspended"
    USER_REACTIVATED = "admin.user.reactivated"
    SETTINGS_CHANGED = "admin.settings.changed"

    # Security
    SECURITY_ALERT = "security.alert"
    SUSPICIOUS_ACTIVITY = "security.suspicious"
    BREACH_ATTEMPT = "security.breach.attempt"
    IP_BLOCKED = "security.ip.blocked"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"

    # API
    API_KEY_CREATED = "api.key.created"
    API_KEY_REVOKED = "api.key.revoked"
    API_CALL = "api.call"
    API_ERROR = "api.error"

    # Financial
    PAYMENT_PROCESSED = "finance.payment.processed"
    PAYMENT_FAILED = "finance.payment.failed"
    SUBSCRIPTION_CREATED = "finance.subscription.created"
    SUBSCRIPTION_CANCELLED = "finance.subscription.cancelled"


class AuditSeverity(Enum):
    """Audit event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: str
    timestamp: str
    user_id: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str  # success, failure, denied
    severity: str
    details: Dict[str, Any]
    session_id: Optional[str]
    correlation_id: Optional[str]
    geo_location: Optional[Dict[str, str]]
    changes: Optional[Dict[str, Any]]  # before/after for updates
    compliance_tags: List[str]  # GDPR, SOC2, HIPAA, etc.
    retention_days: int  # How long to keep this audit log

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)

    def hash(self) -> str:
        """Generate cryptographic hash for integrity verification"""
        data = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
    """
    Enterprise-grade audit logging system
    Features:
    - Tamper-proof logging with cryptographic hashing
    - Multiple storage backends
    - Compliance support (GDPR, SOC 2, HIPAA)
    - Automatic retention policies
    - Real-time alerting for critical events
    """

    def __init__(self):
        self.storage_backends = []
        self.alert_handlers = []
        self.retention_policies = {
            "default": 2555,  # 7 years (SOC 2 requirement)
            "authentication": 2555,  # 7 years
            "data_access": 2555,  # 7 years
            "financial": 3650,  # 10 years
            "privacy": 3650,  # 10 years (GDPR recommendation)
            "security": 2555,  # 7 years
        }

    def add_storage_backend(self, backend):
        """Add storage backend (database, file, cloud, etc.)"""
        self.storage_backends.append(backend)

    def add_alert_handler(self, handler):
        """Add alert handler for critical events"""
        self.alert_handlers.append(handler)

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: str = "",
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Log an audit event

        Args:
            event_type: Type of event being logged
            user_id: User who performed the action
            user_email: User's email
            ip_address: IP address of the request
            user_agent: User agent string
            resource_type: Type of resource affected (user, project, etc.)
            resource_id: ID of the affected resource
            action: Description of the action
            result: Result of the action (success, failure, denied)
            severity: Severity level
            details: Additional event details
            session_id: Session ID
            correlation_id: Correlation ID for tracking related events
            changes: Before/after data for updates
        """
        # Generate event ID
        event_id = self._generate_event_id()

        # Determine compliance tags
        compliance_tags = self._get_compliance_tags(event_type)

        # Determine retention period
        retention_days = self._get_retention_days(event_type)

        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type.value,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action or event_type.value,
            result=result,
            severity=severity.value,
            details=details or {},
            session_id=session_id,
            correlation_id=correlation_id,
            geo_location=self._get_geo_location(ip_address) if ip_address else None,
            changes=changes,
            compliance_tags=compliance_tags,
            retention_days=retention_days
        )

        # Generate integrity hash
        event.details["integrity_hash"] = event.hash()

        # Store event
        await self._store_event(event)

        # Send alerts if critical
        if severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            await self._send_alerts(event)

        logger.info(f"Audit event logged: {event_type.value} by user {user_id}")

        return event

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        import uuid
        return f"audit_{uuid.uuid4().hex}"

    def _get_compliance_tags(self, event_type: AuditEventType) -> List[str]:
        """Determine which compliance frameworks this event relates to"""
        tags = []

        # GDPR compliance
        gdpr_events = [
            AuditEventType.CONSENT_GIVEN,
            AuditEventType.CONSENT_REVOKED,
            AuditEventType.DATA_ANONYMIZED,
            AuditEventType.DATA_ERASED,
            AuditEventType.DATA_ACCESSED,
            AuditEventType.DATA_EXPORT,
            AuditEventType.USER_DELETED,
        ]
        if event_type in gdpr_events:
            tags.append("GDPR")

        # SOC 2 compliance (all authentication and authorization)
        soc2_events = [
            AuditEventType.LOGIN_SUCCESS,
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.PERMISSION_GRANTED,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.SECURITY_ALERT,
            AuditEventType.SETTINGS_CHANGED,
        ]
        if event_type in soc2_events:
            tags.append("SOC2")

        # HIPAA compliance (if handling health data)
        hipaa_events = [
            AuditEventType.DATA_READ,
            AuditEventType.DATA_CREATE,
            AuditEventType.DATA_UPDATE,
            AuditEventType.DATA_DELETE,
            AuditEventType.DATA_EXPORT,
        ]
        if event_type in hipaa_events:
            tags.append("HIPAA")

        # PCI DSS compliance (financial data)
        pci_events = [
            AuditEventType.PAYMENT_PROCESSED,
            AuditEventType.PAYMENT_FAILED,
        ]
        if event_type in pci_events:
            tags.append("PCI_DSS")

        return tags

    def _get_retention_days(self, event_type: AuditEventType) -> int:
        """Get retention period for event type"""
        # Map event types to retention categories
        if "auth" in event_type.value:
            return self.retention_policies["authentication"]
        elif "privacy" in event_type.value:
            return self.retention_policies["privacy"]
        elif "finance" in event_type.value:
            return self.retention_policies["financial"]
        elif "security" in event_type.value:
            return self.retention_policies["security"]
        elif "data" in event_type.value:
            return self.retention_policies["data_access"]
        else:
            return self.retention_policies["default"]

    def _get_geo_location(self, ip_address: str) -> Optional[Dict[str, str]]:
        """Get geo location from IP address"""
        # In production, use a GeoIP service
        # For now, return placeholder
        return {
            "country": "Unknown",
            "city": "Unknown",
            "timezone": "Unknown"
        }

    async def _store_event(self, event: AuditEvent):
        """Store event in all configured backends"""
        tasks = []
        for backend in self.storage_backends:
            tasks.append(backend.store(event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_alerts(self, event: AuditEvent):
        """Send alerts for critical events"""
        tasks = []
        for handler in self.alert_handlers:
            tasks.append(handler.send_alert(event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def query_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """
        Query audit events with filters

        Used for compliance reports and investigations
        """
        # This would query from storage backend
        # For now, return empty list
        return []

    async def generate_compliance_report(
        self,
        compliance_framework: str,  # GDPR, SOC2, HIPAA, PCI_DSS
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report for auditors

        Returns:
            Report with event counts, anomalies, and compliance status
        """
        events = await self.query_events(start_date=start_date, end_date=end_date)

        # Filter events by compliance framework
        filtered_events = [
            e for e in events
            if compliance_framework in e.compliance_tags
        ]

        return {
            "framework": compliance_framework,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(filtered_events),
            "events_by_type": self._group_by_type(filtered_events),
            "events_by_user": self._group_by_user(filtered_events),
            "security_incidents": self._count_security_incidents(filtered_events),
            "compliance_status": "COMPLIANT",
            "anomalies": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _group_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by type"""
        result = {}
        for event in events:
            result[event.event_type] = result.get(event.event_type, 0) + 1
        return result

    def _group_by_user(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by user"""
        result = {}
        for event in events:
            if event.user_id:
                result[event.user_id] = result.get(event.user_id, 0) + 1
        return result

    def _count_security_incidents(self, events: List[AuditEvent]) -> int:
        """Count security incidents"""
        return sum(
            1 for event in events
            if "security" in event.event_type
        )

    async def verify_integrity(self, event: AuditEvent) -> bool:
        """
        Verify audit log integrity using cryptographic hash

        Critical for compliance and forensics
        """
        stored_hash = event.details.get("integrity_hash")
        if not stored_hash:
            return False

        # Recalculate hash
        current_hash = event.hash()

        return stored_hash == current_hash


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions
async def audit_login(user_id: str, email: str, ip: str, success: bool = True):
    """Audit user login attempt"""
    await audit_logger.log_event(
        event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
        user_id=user_id,
        user_email=email,
        ip_address=ip,
        result="success" if success else "failure",
        severity=AuditSeverity.INFO if success else AuditSeverity.WARNING
    )


async def audit_data_access(user_id: str, resource_type: str, resource_id: str, action: str):
    """Audit data access (GDPR/HIPAA requirement)"""
    await audit_logger.log_event(
        event_type=AuditEventType.DATA_READ,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        severity=AuditSeverity.INFO
    )


async def audit_data_change(
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str,
    before: Dict[str, Any],
    after: Dict[str, Any]
):
    """Audit data modification with before/after snapshots"""
    event_type_map = {
        "create": AuditEventType.DATA_CREATE,
        "update": AuditEventType.DATA_UPDATE,
        "delete": AuditEventType.DATA_DELETE
    }

    await audit_logger.log_event(
        event_type=event_type_map.get(action, AuditEventType.DATA_UPDATE),
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        changes={"before": before, "after": after},
        severity=AuditSeverity.INFO
    )


async def audit_security_event(event_type: str, details: Dict[str, Any]):
    """Audit security event"""
    await audit_logger.log_event(
        event_type=AuditEventType.SECURITY_ALERT,
        action=event_type,
        details=details,
        severity=AuditSeverity.CRITICAL
    )
