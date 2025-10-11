"""Persistent audit logging for governance decisions."""

from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Mapping


@dataclass(slots=True)
class AuditEntry:
    """Represents a recorded governance decision."""

    timestamp: float
    action: str
    verdict: str
    payload: Mapping[str, Any]
    notes: str

    def to_row(self) -> tuple[float, str, str, str, str]:
        return (
            self.timestamp,
            self.action,
            self.verdict,
            repr(dict(self.payload)),
            self.notes,
        )


class GovernanceAuditor:
    """Simple SQLite backed audit log used when governance blocks actions."""

    def __init__(self, database_path: str | Path | None = None) -> None:
        base_path = Path(database_path) if database_path else Path(__file__).resolve().parent / "audit.db"
        self.database_path = base_path
        self._lock = threading.RLock()
        self._ensure_schema()

    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    action TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    notes TEXT NOT NULL
                )
                """
            )
            connection.commit()

    # ------------------------------------------------------------------
    def record(self, action: str, verdict: str, payload: Mapping[str, Any], notes: str = "") -> AuditEntry:
        entry = AuditEntry(
            timestamp=time.time(),
            action=action,
            verdict=verdict,
            payload=dict(payload),
            notes=notes,
        )
        with self._lock, sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO audit_log (ts, action, verdict, payload, notes) VALUES (?, ?, ?, ?, ?)",
                entry.to_row(),
            )
            connection.commit()
        return entry

    def list_entries(self) -> List[AuditEntry]:
        with self._lock, sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                "SELECT ts, action, verdict, payload, notes FROM audit_log ORDER BY ts DESC"
            )
            rows = cursor.fetchall()
        entries: List[AuditEntry] = []
        for ts, action, verdict, payload, notes in rows:
            entries.append(
                AuditEntry(
                    timestamp=float(ts),
                    action=str(action),
                    verdict=str(verdict),
                    payload={"raw": str(payload)},
                    notes=str(notes),
                )
            )
        return entries


__all__ = ["AuditEntry", "GovernanceAuditor"]
