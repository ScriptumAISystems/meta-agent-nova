"""gRPC-enabled task queue dispatcher for Nova orchestration."""

from __future__ import annotations

import json
from concurrent import futures
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import grpc

from ..monitoring.logging import log_info
from ..task_queue import proto
from ..task_queue.grpc_service import (
    TaskQueueServicer,
    TaskQueueStub,
    add_TaskQueueServicer_to_server,
    task_queue_channel,
)
from ..task_queue.storage import TaskRecord, TaskRepository


@dataclass(slots=True)
class DispatchedTask:
    """High level view of a queued orchestration task."""

    id: str
    agent: str
    action: str
    payload: Dict[str, object]
    status: str
    attempts: int

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "agent": self.agent,
            "action": self.action,
            "payload": self.payload,
            "status": self.status,
            "attempts": self.attempts,
        }


def _record_to_proto(record: TaskRecord) -> proto.Task:
    task_message = proto.Task()
    task_message.id = record.id
    task_message.type = record.type
    task_message.payload = record.payload
    for key, value in record.metadata.items():
        entry = task_message.metadata.add()
        entry.key = key
        entry.value = value
    task_message.status = record.status
    task_message.created_at = record.created_at
    task_message.updated_at = record.updated_at
    if record.result is not None:
        task_message.result = record.result
    if record.worker_id is not None:
        task_message.worker_id = record.worker_id
    task_message.attempts = record.attempts
    return task_message


def _proto_to_dispatched(message: proto.Task) -> DispatchedTask:
    metadata = {entry.key: entry.value for entry in message.metadata}
    agent, action, payload = _decode_payload(message.payload, metadata)
    return DispatchedTask(
        id=message.id,
        agent=agent,
        action=action,
        payload=payload,
        status=message.status,
        attempts=message.attempts,
    )


def _record_to_dispatched(record: TaskRecord) -> DispatchedTask:
    agent, action, payload = _decode_payload(record.payload, record.metadata)
    return DispatchedTask(
        id=record.id,
        agent=agent,
        action=action,
        payload=payload,
        status=record.status,
        attempts=record.attempts,
    )


def _decode_payload(payload: str, metadata: Dict[str, str]) -> tuple[str, str, Dict[str, object]]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return metadata.get("agent", "unknown"), metadata.get("action", "execute"), {"raw": payload}
    agent = data.get("agent") or metadata.get("agent", "unknown")
    action = data.get("action") or metadata.get("action", "execute")
    payload_data = data.get("payload")
    if isinstance(payload_data, dict):
        payload_dict = payload_data
    elif payload_data is None:
        payload_dict = {k: v for k, v in data.items() if k not in {"agent", "action"}}
    else:
        payload_dict = {"value": payload_data}
    return agent, action, payload_dict


def _encode_payload(agent: str, action: str, payload: Dict[str, object]) -> str:
    return json.dumps({"agent": agent, "action": action, "payload": payload}, sort_keys=True)


class TaskQueueServer(TaskQueueServicer):
    """Minimal gRPC servicer backed by :class:`TaskRepository`."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def Enqueue(self, request: proto.EnqueueRequest, context: grpc.ServicerContext) -> proto.EnqueueResponse:  # noqa: N802
        metadata = {entry.key: entry.value for entry in request.metadata}
        record = self.repository.enqueue(request.type, request.payload, metadata)
        response = proto.EnqueueResponse()
        response.task.CopyFrom(_record_to_proto(record))
        return response

    def Dequeue(self, request: proto.DequeueRequest, context: grpc.ServicerContext) -> proto.DequeueResponse:  # noqa: N802
        worker_id = request.worker_id or "grpc-worker"
        record = self.repository.dequeue(worker_id)
        response = proto.DequeueResponse()
        if record is None:
            response.has_task = False
            return response
        response.has_task = True
        response.task.CopyFrom(_record_to_proto(record))
        return response

    def Ack(self, request: proto.AckRequest, context: grpc.ServicerContext) -> proto.AckResponse:  # noqa: N802
        record = self.repository.ack(request.task_id, request.success, request.result or None)
        response = proto.AckResponse()
        response.task.CopyFrom(_record_to_proto(record))
        return response

    def ListTasks(self, request: proto.ListTasksRequest, context: grpc.ServicerContext) -> proto.ListTasksResponse:  # noqa: N802,E501
        status_filter = request.status or None
        records = self.repository.list_tasks(status=status_filter)
        response = proto.ListTasksResponse()
        for record in records:
            response.tasks.add().CopyFrom(_record_to_proto(record))
        return response


def start_task_queue_server(
    repository: TaskRepository,
    *,
    address: str = "127.0.0.1:50071",
    max_workers: int = 4,
) -> grpc.Server:
    """Start a gRPC task queue server in the background."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_TaskQueueServicer_to_server(TaskQueueServer(repository), server)
    server.add_insecure_port(address)
    server.start()
    log_info(f"Task queue server started on {address}")
    return server


class TaskQueueDispatcher:
    """Client abstraction for dispatching orchestration tasks."""

    def __init__(
        self,
        *,
        address: str | None = None,
        repository_path: str | Path | None = None,
    ) -> None:
        self._repository: TaskRepository | None
        if address:
            self._repository = None
            self._channel = task_queue_channel(address)
            self._stub = TaskQueueStub(self._channel)
        else:
            path = repository_path or ":memory:"
            self._repository = TaskRepository(path)
            self._stub = None
            self._channel = None

    def run_task(self, agent: str, action: str, payload: Optional[Dict[str, object]] = None) -> DispatchedTask:
        payload = payload or {}
        encoded = _encode_payload(agent, action, payload)
        metadata = {"agent": agent, "action": action}
        if self._stub is not None:
            request = proto.EnqueueRequest(type="orchestration", payload=encoded)
            for key, value in metadata.items():
                entry = request.metadata.add()
                entry.key = key
                entry.value = value
            response = self._stub.Enqueue(request)
            return _proto_to_dispatched(response.task)
        assert self._repository is not None  # for type checkers
        record = self._repository.enqueue("orchestration", encoded, metadata)
        return _record_to_dispatched(record)

    def list_tasks(self, status: str | None = None) -> List[DispatchedTask]:
        if self._stub is not None:
            request = proto.ListTasksRequest()
            if status:
                request.status = status
            response = self._stub.ListTasks(request)
            return [_proto_to_dispatched(task) for task in response.tasks]
        assert self._repository is not None
        return [_record_to_dispatched(record) for record in self._repository.list_tasks(status=status)]

    def acknowledge(self, task_id: str, success: bool, result: Optional[str] = None) -> DispatchedTask:
        if self._stub is not None:
            request = proto.AckRequest(task_id=task_id, success=success)
            if result is not None:
                request.result = result
            response = self._stub.Ack(request)
            return _proto_to_dispatched(response.task)
        assert self._repository is not None
        record = self._repository.ack(task_id, success, result)
        return _record_to_dispatched(record)

    def close(self) -> None:
        if self._stub is not None and self._channel is not None:
            self._channel.close()
        if self._repository is not None:
            self._repository.close()


__all__ = [
    "DispatchedTask",
    "TaskQueueDispatcher",
    "TaskQueueServer",
    "start_task_queue_server",
]
