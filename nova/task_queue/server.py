"""Task queue service implementation and server bootstrap utilities."""
from __future__ import annotations

from concurrent import futures
from typing import Dict, Iterable, Optional

import grpc

from . import proto
from .grpc_service import TaskQueueServicer, add_TaskQueueServicer_to_server
from .storage import TASK_STATUSES, TaskRecord, TaskRepository
from ..logging import get_logger
from ..logging.kpi import KPITracker
from ..security.audit import AuditLogger, AuditStore

class TaskQueueService(TaskQueueServicer):
    """Concrete implementation of the task queue gRPC service."""

    def __init__(
        self,
        repository: TaskRepository,
        *,
        kpi_tracker: Optional[KPITracker] = None,
        audit_logger: Optional[AuditLogger] = None,
        visibility_timeout_ms: int = 300_000,
        max_attempts: int = 5,
    ) -> None:
        self._repository = repository
        self._logger = get_logger(__name__)
        self._kpi = kpi_tracker or KPITracker(namespace="task_queue")
        self._audit = audit_logger or AuditLogger(AuditStore(":memory:"))
        self._visibility_timeout_ms = visibility_timeout_ms
        self._max_attempts = max_attempts

    def Enqueue(self, request: proto.EnqueueRequest, context: grpc.ServicerContext) -> proto.EnqueueResponse:  # noqa: N802
        metadata = _metadata_to_dict(request.metadata)
        record = self._repository.enqueue(request.type, request.payload, metadata)
        self._logger.info(
            "Task enqueued",
            extra={"task_id": record.id, "task_type": record.type, "metadata": metadata},
        )
        self._kpi.increment("tasks_enqueued")
        self._audit.record_event("task_enqueued", subject="queue", details={"task_id": record.id})
        return _record_to_proto(record)

    def Dequeue(self, request: proto.DequeueRequest, context: grpc.ServicerContext) -> proto.DequeueResponse:  # noqa: N802
        requeued, failed = self._repository.recover_overdue_tasks(
            self._visibility_timeout_ms,
            max_attempts=self._max_attempts,
        )
        if requeued:
            self._kpi.increment("tasks_retried", len(requeued))
            for record in requeued:
                self._logger.warning(
                    "Requeued stale task",
                    extra={"task_id": record.id, "attempts": record.attempts},
                )
                self._audit.record_event(
                    "task_requeued",
                    subject="queue",
                    details={"task_id": record.id, "attempts": str(record.attempts)},
                )
        if failed:
            self._kpi.increment("tasks_failed_timeout", len(failed))
            for record in failed:
                self._logger.error(
                    "Task marked as failed after exceeding attempts",
                    extra={"task_id": record.id, "attempts": record.attempts},
                )
                self._audit.record_event(
                    "task_failed_timeout",
                    subject=record.worker_id or "unknown",
                    details={"task_id": record.id, "attempts": str(record.attempts)},
                )
        record = self._repository.dequeue(request.worker_id)
        response = proto.DequeueResponse()
        if record is None:
            response.has_task = False
            return response
        response.has_task = True
        response.task.CopyFrom(_record_to_proto(record).task)
        self._logger.info(
            "Task dispatched",
            extra={"task_id": record.id, "worker_id": request.worker_id},
        )
        self._kpi.increment("tasks_dispatched")
        self._audit.record_event("task_dequeued", subject=request.worker_id, details={"task_id": record.id})
        return response

    def Ack(self, request: proto.AckRequest, context: grpc.ServicerContext) -> proto.AckResponse:  # noqa: N802
        record = self._repository.ack(request.task_id, request.success, request.result or None)
        metric = "tasks_completed" if request.success else "tasks_failed"
        self._kpi.increment(metric)
        self._logger.info(
            "Task acknowledged",
            extra={
                "task_id": record.id,
                "status": record.status,
                "result": record.result,
            },
        )
        self._audit.record_event(
            "task_acknowledged",
            subject=record.worker_id or "unknown",
            details={"task_id": record.id, "status": record.status},
        )
        return _record_to_proto(record)

    def ListTasks(self, request: proto.ListTasksRequest, context: grpc.ServicerContext) -> proto.ListTasksResponse:  # noqa: N802
        status_filter = request.status or None
        if status_filter and status_filter not in TASK_STATUSES:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Unsupported status {status_filter}")
        response = proto.ListTasksResponse()
        for record in self._repository.list_tasks(status_filter):
            response.tasks.append(_record_to_proto(record).task)
        return response


class TaskQueueServer:
    """Utility class for running the task queue gRPC server."""

    def __init__(
        self,
        service: TaskQueueService,
        *,
        host: str = "0.0.0.0",
        port: int = 50051,
        max_workers: int = 10,
    ) -> None:
        self._service = service
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        add_TaskQueueServicer_to_server(service, self._server)
        bound_port = self._server.add_insecure_port(f"{host}:{port}")
        if bound_port == 0:
            raise RuntimeError("Failed to bind gRPC server to port")
        self._host = host
        self._port = bound_port
        self._logger = get_logger(__name__)

    def start(self) -> None:
        self._logger.info("Starting task queue server")
        self._server.start()

    def wait_for_termination(self) -> None:
        self._server.wait_for_termination()

    def stop(self, grace: Optional[float] = None) -> None:
        self._logger.info("Stopping task queue server")
        self._server.stop(grace).wait()

    @property
    def address(self) -> str:
        return f"{self._host}:{self._port}"


def _metadata_to_dict(entries: Iterable[proto.TaskMetadataEntry]) -> Dict[str, str]:
    return {entry.key: entry.value for entry in entries}


def _record_to_proto(record: TaskRecord) -> proto.EnqueueResponse:
    task_message = proto.Task()
    task_message.id = record.id
    task_message.type = record.type
    task_message.payload = record.payload
    task_message.status = record.status
    task_message.created_at = record.created_at
    task_message.updated_at = record.updated_at
    if record.result is not None:
        task_message.result = record.result
    if record.worker_id is not None:
        task_message.worker_id = record.worker_id
    task_message.attempts = record.attempts
    for key, value in record.metadata.items():
        entry = task_message.metadata.add()
        entry.key = key
        entry.value = value

    response = proto.EnqueueResponse()
    response.task.CopyFrom(task_message)
    return response


__all__ = ["TaskQueueService", "TaskQueueServer"]
