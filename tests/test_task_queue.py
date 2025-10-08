"""Integration tests for the gRPC task queue."""
from __future__ import annotations

import grpc

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

    dequeue_request = proto.DequeueRequest()
    dequeue_request.worker_id = "worker-1"
    dequeue_response = stub.Dequeue(dequeue_request)
    assert dequeue_response.has_task is True
    assert dequeue_response.task.id == task_id

    ack_request = proto.AckRequest()
    ack_request.task_id = task_id
    ack_request.success = True
    ack_request.result = "done"
    ack_response = stub.Ack(ack_request)
    assert ack_response.task.status == "COMPLETED"

    list_request = proto.ListTasksRequest()
    list_response = stub.ListTasks(list_request)
    assert any(task.id == task_id for task in list_response.tasks)

    channel.close()
    server.stop(0)
