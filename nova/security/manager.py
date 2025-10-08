"""Security orchestration utilities for Nova."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..logging import get_logger
from .audit import AuditLogger, AuditStore
from .compliance import ComplianceRegistry, ControlEvidence


@dataclass
class SecurityContext:
    """Carries identity and contextual metadata for authorization checks."""

    subject: str
    action: str
    resource: str
    metadata: Dict[str, str]


class SecurityManager:
    """Coordinates audit logging and ISO 27001 compliance tracking."""

    def __init__(self, audit_store: Optional[AuditStore] = None) -> None:
        self._audit_store = audit_store or AuditStore(":memory:")
        self._audit_logger = AuditLogger(self._audit_store)
        self._compliance = ComplianceRegistry()
        self._logger = get_logger("nova.security.manager")

    @property
    def audits(self) -> AuditLogger:
        return self._audit_logger

    @property
    def compliance_registry(self) -> ComplianceRegistry:
        return self._compliance

    def register_control(self, evidence: ControlEvidence) -> None:
        self._compliance.register(evidence)
        self._logger.info("Control registered", extra={"control_id": evidence.control_id})

    def record_security_event(self, event_type: str, *, subject: str, details: Optional[Dict[str, str]] = None) -> None:
        self._audit_logger.record_event(event_type, subject=subject, details=details)


__all__ = ["SecurityManager", "SecurityContext"]
