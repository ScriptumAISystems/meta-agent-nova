"""Security and audit logging utilities aligned with ISO 27001."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..logging import get_logger


@dataclass(frozen=True)
class AuditEvent:
    """Represents a security relevant event."""

    event_type: str
    subject: str
    details: Dict[str, str]
    created_at: int


class AuditStore:
    """Durable storage for audit events using SQLite."""

    def __init__(self, database_path: str | Path = ":memory:") -> None:
        self._database_path = str(database_path)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._logger = get_logger(__name__)
        self._create_schema()

    def _create_schema(self) -> None:
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )

    def append(self, event: AuditEvent) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO audit_events (event_type, subject, details, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    event.subject,
                    json.dumps(event.details, sort_keys=True),
                    event.created_at,
                ),
            )

    def list_events(self, limit: int = 100) -> list[AuditEvent]:
        cursor = self._connection.execute(
            "SELECT event_type, subject, details, created_at FROM audit_events ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        events = []
        for row in cursor.fetchall():
            events.append(
                AuditEvent(
                    event_type=row["event_type"],
                    subject=row["subject"],
                    details=json.loads(row["details"]),
                    created_at=row["created_at"],
                )
            )
        return events

    def close(self) -> None:
        self._connection.close()


class AuditLogger:
    """High level helper for persisting audit events and emitting logs."""

    def __init__(self, store: AuditStore) -> None:
        self._store = store
        self._logger = get_logger("nova.security.audit")

    def record_event(self, event_type: str, *, subject: str, details: Optional[Dict[str, str]] = None) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            subject=subject,
            details=details or {},
            created_at=int(time.time() * 1000),
        )
        self._store.append(event)
        self._logger.info("Audit event", extra={"event_type": event_type, "subject": subject, "details": event.details})
        return event


__all__ = ["AuditEvent", "AuditLogger", "AuditStore"]
