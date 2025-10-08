"""gRPC service definitions for the Nova task queue."""
from __future__ import annotations

import grpc

from . import proto


class TaskQueueStub:
    """Client-side stub for interacting with the task queue service."""

    def __init__(self, channel: grpc.Channel) -> None:
        self.Enqueue = channel.unary_unary(
            "/nova.taskqueue.TaskQueue/Enqueue",
            request_serializer=proto.EnqueueRequest.SerializeToString,
            response_deserializer=proto.EnqueueResponse.FromString,
        )
        self.Dequeue = channel.unary_unary(
            "/nova.taskqueue.TaskQueue/Dequeue",
            request_serializer=proto.DequeueRequest.SerializeToString,
            response_deserializer=proto.DequeueResponse.FromString,
        )
        self.Ack = channel.unary_unary(
            "/nova.taskqueue.TaskQueue/Ack",
            request_serializer=proto.AckRequest.SerializeToString,
            response_deserializer=proto.AckResponse.FromString,
        )
        self.ListTasks = channel.unary_unary(
            "/nova.taskqueue.TaskQueue/ListTasks",
            request_serializer=proto.ListTasksRequest.SerializeToString,
            response_deserializer=proto.ListTasksResponse.FromString,
        )


class TaskQueueServicer:
    """Server-side base implementation.

    Concrete services should subclass this base and implement the RPC methods.
    """

    def Enqueue(self, request: proto.EnqueueRequest, context: grpc.ServicerContext) -> proto.EnqueueResponse:  # noqa: N802
        raise NotImplementedError

    def Dequeue(self, request: proto.DequeueRequest, context: grpc.ServicerContext) -> proto.DequeueResponse:  # noqa: N802
        raise NotImplementedError

    def Ack(self, request: proto.AckRequest, context: grpc.ServicerContext) -> proto.AckResponse:  # noqa: N802
        raise NotImplementedError

    def ListTasks(self, request: proto.ListTasksRequest, context: grpc.ServicerContext) -> proto.ListTasksResponse:  # noqa: N802
        raise NotImplementedError


def add_TaskQueueServicer_to_server(servicer: TaskQueueServicer, server: grpc.Server) -> None:  # noqa: N802
    rpc_method_handlers = {
        "Enqueue": grpc.unary_unary_rpc_method_handler(
            servicer.Enqueue,
            request_deserializer=proto.EnqueueRequest.FromString,
            response_serializer=proto.EnqueueResponse.SerializeToString,
        ),
        "Dequeue": grpc.unary_unary_rpc_method_handler(
            servicer.Dequeue,
            request_deserializer=proto.DequeueRequest.FromString,
            response_serializer=proto.DequeueResponse.SerializeToString,
        ),
        "Ack": grpc.unary_unary_rpc_method_handler(
            servicer.Ack,
            request_deserializer=proto.AckRequest.FromString,
            response_serializer=proto.AckResponse.SerializeToString,
        ),
        "ListTasks": grpc.unary_unary_rpc_method_handler(
            servicer.ListTasks,
            request_deserializer=proto.ListTasksRequest.FromString,
            response_serializer=proto.ListTasksResponse.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "nova.taskqueue.TaskQueue", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))


def task_queue_channel(address: str) -> grpc.Channel:
    """Create an insecure gRPC channel for the task queue service."""
    return grpc.insecure_channel(address)


__all__ = [
    "TaskQueueStub",
    "TaskQueueServicer",
    "add_TaskQueueServicer_to_server",
    "task_queue_channel",
]
