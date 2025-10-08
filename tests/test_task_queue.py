"""Integration tests for the gRPC task queue."""
from __future__ import annotations

import grpc
import time

from nova.logging import initialize_logging
from nova.task_queue import TaskQueueServer, TaskQueueService, TaskRepository, TaskQueueStub
from nova.task_queue import proto


def test_task_queue_lifecycle() -> None:
    initialize_logging(log_level="CRITICAL")
    repository = TaskRepository()
    service = TaskQueueService(repository)
    server = TaskQueueServer(service, host="localhost", port=0)
    server.start()
    channel = grpc.insecure_channel(server.address)
    grpc.channel_ready_future(channel).result(timeout=5)
    stub = TaskQueueStub(channel)

    enqueue_request = proto.EnqueueRequest()
    enqueue_request.type = "test"
    enqueue_request.payload = "payload"
    enqueue_request.metadata.add(key="priority", value="high")
    enqueue_response = stub.Enqueue(enqueue_request)
    task_id = enqueue_response.task.id
    assert enqueue_response.task.attempts == 0

    dequeue_request = proto.DequeueRequest()
    dequeue_request.worker_id = "worker-1"
    dequeue_response = stub.Dequeue(dequeue_request)
    assert dequeue_response.has_task is True
    assert dequeue_response.task.id == task_id
    assert dequeue_response.task.attempts == 1

    ack_request = proto.AckRequest()
    ack_request.task_id = task_id
    ack_request.success = True
    ack_request.result = "done"
    ack_response = stub.Ack(ack_request)
    assert ack_response.task.status == "COMPLETED"
    assert ack_response.task.attempts == 1

    list_request = proto.ListTasksRequest()
    list_response = stub.ListTasks(list_request)
    assert any(task.id == task_id for task in list_response.tasks)

    channel.close()
    server.stop(0)


def test_repository_recovers_overdue_tasks() -> None:
    repository = TaskRepository()
    task = repository.enqueue("demo", "payload")
    in_progress = repository.dequeue("worker-1")
    assert in_progress is not None
    assert in_progress.attempts == 1

    requeued, failed = repository.recover_overdue_tasks(-1, max_attempts=3)
    assert failed == []
    assert len(requeued) == 1
    assert requeued[0].id == task.id
    assert requeued[0].status == "PENDING"
    assert requeued[0].worker_id is None
    assert requeued[0].attempts == 1

    second_claim = repository.dequeue("worker-2")
    assert second_claim is not None
    assert second_claim.worker_id == "worker-2"
    assert second_claim.attempts == 2

    _, failed_final = repository.recover_overdue_tasks(-1, max_attempts=2)
    assert len(failed_final) == 1
    assert failed_final[0].status == "FAILED"
    assert failed_final[0].result == "maximum attempts exceeded"
    all_failed = repository.list_tasks("FAILED")
    assert all_failed[0].id == task.id


def test_service_requeues_after_visibility_timeout() -> None:
    initialize_logging(log_level="CRITICAL")
    repository = TaskRepository()
    service = TaskQueueService(repository, visibility_timeout_ms=5, max_attempts=2)
    server = TaskQueueServer(service, host="localhost", port=0)
    server.start()
    channel = grpc.insecure_channel(server.address)
    grpc.channel_ready_future(channel).result(timeout=5)
    stub = TaskQueueStub(channel)

    enqueue_request = proto.EnqueueRequest()
    enqueue_request.type = "retry"
    enqueue_request.payload = "payload"
    stub.Enqueue(enqueue_request)

    dequeue_request = proto.DequeueRequest()
    dequeue_request.worker_id = "worker-1"
    first = stub.Dequeue(dequeue_request)
    assert first.has_task is True
    assert first.task.worker_id == "worker-1"
    assert first.task.attempts == 1

    time.sleep(0.01)

    dequeue_request.worker_id = "worker-2"
    second = stub.Dequeue(dequeue_request)
    assert second.has_task is True
    assert second.task.worker_id == "worker-2"
    assert second.task.attempts == 2

    ack_request = proto.AckRequest()
    ack_request.task_id = second.task.id
    ack_request.success = True
    stub.Ack(ack_request)

    channel.close()
    server.stop(0)


def test_service_marks_tasks_failed_after_max_attempts() -> None:
    initialize_logging(log_level="CRITICAL")
    repository = TaskRepository()
    service = TaskQueueService(repository, visibility_timeout_ms=5, max_attempts=1)
    server = TaskQueueServer(service, host="localhost", port=0)
    server.start()
    channel = grpc.insecure_channel(server.address)
    grpc.channel_ready_future(channel).result(timeout=5)
    stub = TaskQueueStub(channel)

    enqueue_request = proto.EnqueueRequest()
    enqueue_request.type = "exhaust"
    enqueue_request.payload = "payload"
    stub.Enqueue(enqueue_request)

    dequeue_request = proto.DequeueRequest()
    dequeue_request.worker_id = "worker-1"
    first = stub.Dequeue(dequeue_request)
    assert first.has_task is True
    assert first.task.attempts == 1

    time.sleep(0.01)

    dequeue_request.worker_id = "worker-2"
    second = stub.Dequeue(dequeue_request)
    assert second.has_task is False

    list_request = proto.ListTasksRequest()
    list_request.status = "FAILED"
    failed = stub.ListTasks(list_request)
    assert len(failed.tasks) == 1
    assert failed.tasks[0].status == "FAILED"
    assert failed.tasks[0].result == "maximum attempts exceeded"
    assert failed.tasks[0].attempts == 1

    channel.close()
    server.stop(0)
