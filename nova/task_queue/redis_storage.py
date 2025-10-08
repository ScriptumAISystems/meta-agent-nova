"""Redis-backed task repository for the Nova task queue."""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - import is optional for real Redis deployments
    from redis import Redis  # type: ignore
    from redis.client import Pipeline  # type: ignore
except Exception:  # pragma: no cover - fall back to dynamic typing
    Redis = Any  # type: ignore
    Pipeline = Any  # type: ignore

from ..logging import get_logger
from .storage import TASK_STATUSES, TaskRecord

_UNSET = object()


class RedisTaskRepository:
    """Persistence layer that stores queue data in Redis."""

    def __init__(
        self,
        client: Redis,
        *,
        namespace: str = "nova_task_queue",
    ) -> None:
        self._client = client
        self._namespace = namespace
        self._logger = get_logger(__name__)

    # -- public api -----------------------------------------------------
    def close(self) -> None:  # pragma: no cover - required for interface parity
        """Compatibility shim for the sqlite repository."""

    def enqueue(
        self,
        task_type: str,
        payload: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> TaskRecord:
        metadata = metadata or {}
        now = self._now()
        task_id = str(uuid.uuid4())
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
        task_key = self._task_key(task_id)
        with self._client.pipeline(transaction=True) as pipe:
            pipe.hset(
                task_key,
                mapping={
                    "id": record.id,
                    "type": record.type,
                    "payload": record.payload,
                    "metadata": json.dumps(record.metadata, sort_keys=True),
                    "status": record.status,
                    "created_at": record.created_at,
                    "updated_at": record.updated_at,
                    "result": "",
                    "worker_id": "",
                    "attempts": record.attempts,
                },
            )
            pipe.sadd(self._all_tasks_key, record.id)
            pipe.zadd(self._pending_key, {record.id: float(record.created_at)})
            self._transition_status(pipe, None, "PENDING", record.id)
            pipe.execute()
        self._logger.debug(
            "Enqueued task in Redis",
            extra={"task_id": record.id, "task_type": record.type},
        )
        return record

    def dequeue(self, worker_id: str) -> Optional[TaskRecord]:
        popped = self._client.zpopmin(self._pending_key, count=1)
        if not popped:
            return None
        task_id = self._decode(popped[0][0])
        now = self._now()
        data = self._client.hgetall(self._task_key(task_id))
        if not data:
            return None
        attempts = self._as_int(data.get("attempts"), default=0) + 1
        with self._client.pipeline(transaction=True) as pipe:
            pipe.hset(
                self._task_key(task_id),
                mapping={
                    "status": "IN_PROGRESS",
                    "updated_at": now,
                    "worker_id": worker_id,
                    "attempts": attempts,
                },
            )
            pipe.zadd(self._in_progress_key, {task_id: float(now)})
            self._transition_status(pipe, "PENDING", "IN_PROGRESS", task_id)
            pipe.execute()
        record = self._record_from_data(
            data,
            id=task_id,
            status="IN_PROGRESS",
            updated_at=now,
            worker_id=worker_id,
            attempts=attempts,
        )
        self._logger.debug(
            "Dispatched task from Redis queue",
            extra={"task_id": record.id, "worker_id": worker_id, "attempts": attempts},
        )
        return record

    def ack(self, task_id: str, success: bool, result: Optional[str]) -> TaskRecord:
        data = self._client.hgetall(self._task_key(task_id))
        if not data:
            raise KeyError(f"Task {task_id} does not exist")
        now = self._now()
        status = "COMPLETED" if success else "FAILED"
        result_value = result or ""
        with self._client.pipeline(transaction=True) as pipe:
            pipe.hset(
                self._task_key(task_id),
                mapping={
                    "status": status,
                    "updated_at": now,
                    "result": result_value,
                },
            )
            pipe.zrem(self._in_progress_key, task_id)
            self._transition_status(pipe, "IN_PROGRESS", status, task_id)
            pipe.execute()
        return self._record_from_data(
            data,
            id=task_id,
            status=status,
            updated_at=now,
            result=result_value or None,
        )

    def list_tasks(self, status: Optional[str] = None) -> List[TaskRecord]:
        if status and status not in TASK_STATUSES:
            raise ValueError(f"Unsupported status {status!r}")
        if status:
            ids = self._client.smembers(self._status_key(status))
        else:
            ids = self._client.smembers(self._all_tasks_key)
        records = []
        for raw_id in ids:
            task_id = self._decode(raw_id)
            data = self._client.hgetall(self._task_key(task_id))
            if not data:
                continue
            record = self._record_from_data(data, id=task_id)
            if status is None or record.status == status:
                records.append(record)
        records.sort(key=lambda rec: rec.created_at)
        return records

    def heartbeat(self, task_id: str) -> None:
        now = self._now()
        with self._client.pipeline(transaction=True) as pipe:
            pipe.hset(self._task_key(task_id), mapping={"updated_at": now})
            pipe.zadd(self._in_progress_key, {task_id: float(now)})
            pipe.execute()

    def recover_overdue_tasks(
        self,
        max_age_ms: int,
        *,
        max_attempts: int,
    ) -> tuple[List[TaskRecord], List[TaskRecord]]:
        threshold = self._now() - max_age_ms
        overdue = self._client.zrangebyscore(self._in_progress_key, 0, threshold)
        if not overdue:
            return [], []
        requeued: List[TaskRecord] = []
        failed: List[TaskRecord] = []
        for raw_id in overdue:
            task_id = self._decode(raw_id)
            data = self._client.hgetall(self._task_key(task_id))
            if not data:
                self._client.zrem(self._in_progress_key, task_id)
                continue
            attempts = self._as_int(data.get("attempts"), default=0)
            now = self._now()
            if attempts >= max_attempts:
                with self._client.pipeline(transaction=True) as pipe:
                    pipe.hset(
                        self._task_key(task_id),
                        mapping={
                            "status": "FAILED",
                            "updated_at": now,
                            "result": "maximum attempts exceeded",
                        },
                    )
                    pipe.zrem(self._in_progress_key, task_id)
                    self._transition_status(pipe, "IN_PROGRESS", "FAILED", task_id)
                    pipe.execute()
                failed.append(
                    self._record_from_data(
                        data,
                        id=task_id,
                        status="FAILED",
                        updated_at=now,
                        result="maximum attempts exceeded",
                    )
                )
            else:
                with self._client.pipeline(transaction=True) as pipe:
                    pipe.hset(
                        self._task_key(task_id),
                        mapping={
                            "status": "PENDING",
                            "updated_at": now,
                            "worker_id": "",
                        },
                    )
                    pipe.zrem(self._in_progress_key, task_id)
                    pipe.zadd(self._pending_key, {task_id: float(now)})
                    self._transition_status(pipe, "IN_PROGRESS", "PENDING", task_id)
                    pipe.execute()
                requeued.append(
                    self._record_from_data(
                        data,
                        id=task_id,
                        status="PENDING",
                        updated_at=now,
                        worker_id=None,
                    )
                )
        return requeued, failed

    # -- helpers --------------------------------------------------------
    @property
    def _all_tasks_key(self) -> str:
        return f"{self._namespace}:all"

    @property
    def _pending_key(self) -> str:
        return f"{self._namespace}:pending"

    @property
    def _in_progress_key(self) -> str:
        return f"{self._namespace}:in_progress"

    def _status_key(self, status: str) -> str:
        return f"{self._namespace}:status:{status.lower()}"

    def _task_key(self, task_id: str) -> str:
        return f"{self._namespace}:task:{task_id}"

    def _transition_status(
        self,
        pipe: Any,
        previous: Optional[str],
        new: Optional[str],
        task_id: str,
    ) -> None:
        if previous and previous in TASK_STATUSES:
            pipe.srem(self._status_key(previous), task_id)
        if new and new in TASK_STATUSES:
            pipe.sadd(self._status_key(new), task_id)

    @staticmethod
    def _now() -> int:
        return int(time.time() * 1000)

    def _record_from_data(
        self,
        data: Dict[str, object],
        *,
        id: str,
        status: Optional[str] = None,
        updated_at: Optional[int] = None,
        result: Optional[str] = None,
        worker_id: Optional[str] | object = _UNSET,
        attempts: Optional[int] = None,
    ) -> TaskRecord:
        base = {key: self._decode(value) for key, value in data.items()}
        resolved_worker: Optional[str]
        if worker_id is _UNSET:
            resolved_worker = base.get("worker_id") or None
        else:
            resolved_worker = worker_id  # type: ignore[assignment]
        record = TaskRecord(
            id=id,
            type=base.get("type", ""),
            payload=base.get("payload", ""),
            metadata=json.loads(base.get("metadata", "{}") or "{}"),
            status=status or base.get("status", "PENDING"),
            created_at=self._as_int(base.get("created_at"), default=self._now()),
            updated_at=(
                updated_at
                if updated_at is not None
                else self._as_int(base.get("updated_at"), default=self._now())
            ),
            result=(result if result is not None else base.get("result") or None),
            worker_id=resolved_worker,
            attempts=(
                attempts
                if attempts is not None
                else self._as_int(base.get("attempts"), default=0)
            ),
        )
        return record

    @staticmethod
    def _decode(value: object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if value is None:
            return ""
        return str(value)

    def _as_int(self, value: object, *, default: int) -> int:
        raw = self._decode(value)
        if not raw:
            return default
        try:
            return int(raw)
        except (TypeError, ValueError):
            return default


class InMemoryRedis:
    """Lightweight Redis-compatible store for tests and local development."""

    def __init__(self) -> None:
        self._hashes: Dict[str, Dict[str, Any]] = {}
        self._sorted_sets: Dict[str, Dict[str, float]] = {}
        self._sets: Dict[str, set[str]] = {}

    # -- generic operations -------------------------------------------------
    def close(self) -> None:  # pragma: no cover - included for API parity
        return None

    def hset(self, key: str, *, mapping: Dict[str, Any]) -> None:
        target = self._hashes.setdefault(key, {})
        target.update(mapping)

    def hgetall(self, key: str) -> Dict[str, Any]:
        return dict(self._hashes.get(key, {}))

    def zadd(self, key: str, mapping: Dict[str, float]) -> None:
        target = self._sorted_sets.setdefault(key, {})
        for member, score in mapping.items():
            target[str(member)] = float(score)

    def zpopmin(self, key: str, count: int = 1) -> List[tuple[str, float]]:
        target = self._sorted_sets.get(key, {})
        if not target:
            return []
        ordered = sorted(target.items(), key=lambda item: (item[1], item[0]))
        popped: List[tuple[str, float]] = []
        for member, score in ordered[:count]:
            popped.append((member, score))
            del target[member]
        return popped

    def zrangebyscore(self, key: str, min_score: float, max_score: float) -> List[str]:
        target = self._sorted_sets.get(key, {})
        return [member for member, score in target.items() if min_score <= score <= max_score]

    def zrem(self, key: str, member: str) -> int:
        target = self._sorted_sets.get(key, {})
        if member in target:
            del target[member]
            return 1
        return 0

    def sadd(self, key: str, *members: str) -> int:
        target = self._sets.setdefault(key, set())
        before = len(target)
        for member in members:
            target.add(member)
        return len(target) - before

    def smembers(self, key: str) -> set[str]:
        return set(self._sets.get(key, set()))

    def srem(self, key: str, *members: str) -> int:
        target = self._sets.get(key, set())
        removed = 0
        for member in members:
            if member in target:
                target.remove(member)
                removed += 1
        return removed

    def pipeline(self, transaction: bool = True) -> "_InMemoryPipeline":
        return _InMemoryPipeline(self)


class _InMemoryPipeline:
    """Minimal pipeline implementation that proxies to :class:`InMemoryRedis`."""

    def __init__(self, backend: InMemoryRedis) -> None:
        self._backend = backend

    # context manager protocol ------------------------------------------------
    def __enter__(self) -> "_InMemoryPipeline":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - no cleanup needed
        return None

    # redis operations --------------------------------------------------------
    def hset(self, key: str, *, mapping: Dict[str, Any]) -> "_InMemoryPipeline":
        self._backend.hset(key, mapping=mapping)
        return self

    def zadd(self, key: str, mapping: Dict[str, float]) -> "_InMemoryPipeline":
        self._backend.zadd(key, mapping)
        return self

    def sadd(self, key: str, *members: str) -> "_InMemoryPipeline":
        self._backend.sadd(key, *members)
        return self

    def srem(self, key: str, *members: str) -> "_InMemoryPipeline":
        self._backend.srem(key, *members)
        return self

    def zrem(self, key: str, member: str) -> "_InMemoryPipeline":
        self._backend.zrem(key, member)
        return self

    def execute(self) -> List[None]:  # pragma: no cover - deterministic return
        return []


__all__ = ["RedisTaskRepository", "InMemoryRedis"]
