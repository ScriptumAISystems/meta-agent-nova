"""SQLite-backed storage for the Nova task queue service."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, cast

_UNSET = object()

from ..logging import get_logger


TASK_STATUSES = {
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
}


@dataclass(frozen=True)
class TaskRecord:
    """Represents the state of a task stored in the repository."""

    id: str
    type: str
    payload: str
    metadata: Dict[str, str]
    status: str
    created_at: int
    updated_at: int
    result: Optional[str]
    worker_id: Optional[str]
    attempts: int


class TaskRepository:
    """Thread-safe persistence layer for queue tasks."""

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
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    result TEXT,
                    worker_id TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            columns = {
                row["name"]
                for row in self._connection.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "attempts" not in columns:
                self._connection.execute(
                    "ALTER TABLE tasks ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0"
                )

    def close(self) -> None:
        self._connection.close()

    def enqueue(self, task_type: str, payload: str, metadata: Optional[Dict[str, str]] = None) -> TaskRecord:
        metadata = metadata or {}
        task_id = str(uuid.uuid4())
        now = self._now()
        record = TaskRecord(
            id=task_id,
            type=task_type,
            payload=payload,
            metadata=metadata,
            status="PENDING",
            created_at=now,
            updated_at=now,
            result=None,
            worker_id=None,
            attempts=0,
        )
        self._logger.debug("Persisting new task", extra={"task_id": task_id, "task_type": task_type})
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO tasks (id, type, payload, metadata, status, created_at, updated_at, result, worker_id, attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.type,
                    record.payload,
                    json.dumps(record.metadata, sort_keys=True),
                    record.status,
                    record.created_at,
                    record.updated_at,
                    record.result,
                    record.worker_id,
                    record.attempts,
                ),
            )
        return record

    def dequeue(self, worker_id: str) -> Optional[TaskRecord]:
        with self._lock:
            cursor = self._connection.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row is None:
                return None
            now = self._now()
            self._connection.execute(
                """
                UPDATE tasks
                SET status = 'IN_PROGRESS', updated_at = ?, worker_id = ?, attempts = attempts + 1
                WHERE id = ?
                """,
                (now, worker_id, row["id"]),
            )
            self._connection.commit()
        return self._row_to_record(
            row,
            status="IN_PROGRESS",
            worker_id=worker_id,
            updated_at=now,
            attempts=row["attempts"] + 1,
        )

    def ack(self, task_id: str, success: bool, result: Optional[str]) -> TaskRecord:
        target_status = "COMPLETED" if success else "FAILED"
        now = self._now()
        with self._lock, self._connection:
            cursor = self._connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Task {task_id} does not exist")
            self._connection.execute(
                """
                UPDATE tasks
                SET status = ?, updated_at = ?, result = ?
                WHERE id = ?
                """,
                (target_status, now, result, task_id),
            )
        return self._row_to_record(row, status=target_status, updated_at=now, result=result)

    def list_tasks(self, status: Optional[str] = None) -> List[TaskRecord]:
        query = "SELECT * FROM tasks"
        params: Iterable[object] = ()
        if status:
            if status not in TASK_STATUSES:
                raise ValueError(f"Unsupported status {status!r}")
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at ASC"
        cursor = self._connection.execute(query, params)
        return [self._row_to_record(row) for row in cursor.fetchall()]

    def heartbeat(self, task_id: str) -> None:
        """Refresh the updated timestamp for a task currently being processed."""
        now = self._now()
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE tasks SET updated_at = ? WHERE id = ?", (now, task_id)
            )

    def recover_overdue_tasks(
        self,
        max_age_ms: int,
        *,
        max_attempts: int,
    ) -> tuple[List[TaskRecord], List[TaskRecord]]:
        """Requeue or fail tasks that exceeded the visibility timeout.

        Returns a tuple of (requeued_records, failed_records).
        """
        threshold = self._now() - max_age_ms
        requeued: List[TaskRecord] = []
        failed: List[TaskRecord] = []
        with self._lock:
            cursor = self._connection.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'IN_PROGRESS' AND updated_at < ?
                """,
                (threshold,),
            )
            rows = cursor.fetchall()
            if not rows:
                return requeued, failed
            now = self._now()
            for row in rows:
                record_attempts = row["attempts"]
                if record_attempts >= max_attempts:
                    self._connection.execute(
                        """
                        UPDATE tasks
                        SET status = 'FAILED', updated_at = ?, result = ?
                        WHERE id = ?
                        """,
                        (
                            now,
                            "maximum attempts exceeded",
                            row["id"],
                        ),
                    )
                    failed.append(
                        self._row_to_record(
                            row,
                            status="FAILED",
                            updated_at=now,
                            result="maximum attempts exceeded",
                        )
                    )
                else:
                    self._connection.execute(
                        """
                        UPDATE tasks
                        SET status = 'PENDING', updated_at = ?, worker_id = NULL
                        WHERE id = ?
                        """,
                        (now, row["id"]),
                    )
                    requeued.append(
                        self._row_to_record(
                            row,
                            status="PENDING",
                            updated_at=now,
                            worker_id=None,
                        )
                    )
            self._connection.commit()
        return requeued, failed

    @staticmethod
    def _now() -> int:
        return int(time.time() * 1000)

    def _row_to_record(
        self,
        row: sqlite3.Row,
        *,
        status: Optional[str] = None,
        updated_at: Optional[int] = None,
        result: Optional[str] = None,
        worker_id: Optional[str] | object = _UNSET,
        attempts: Optional[int] = None,
    ) -> TaskRecord:
        resolved_worker: Optional[str]
        if worker_id is _UNSET:
            resolved_worker = row["worker_id"]
        else:
            resolved_worker = cast(Optional[str], worker_id)
        return TaskRecord(
            id=row["id"],
            type=row["type"],
            payload=row["payload"],
            metadata=json.loads(row["metadata"]),
            status=status or row["status"],
            created_at=row["created_at"],
            updated_at=updated_at or row["updated_at"],
            result=result if result is not None else row["result"],
            worker_id=resolved_worker,
            attempts=attempts if attempts is not None else row["attempts"],
        )


__all__ = ["TaskRepository", "TaskRecord", "TASK_STATUSES"]
