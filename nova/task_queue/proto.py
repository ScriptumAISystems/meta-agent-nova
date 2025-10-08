"""Dynamic protocol buffer definitions for the Nova task queue service."""
from __future__ import annotations

from google.protobuf import (
    descriptor_pb2,
    descriptor_pool,
    message as _message,
    reflection as _reflection,
    symbol_database as _symbol_database,
)


def _build_file_descriptor() -> descriptor_pb2.FileDescriptorProto:
    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "task_queue.proto"
    file_proto.package = "nova.taskqueue"
    file_proto.syntax = "proto3"

    # TaskMetadataEntry message
    metadata_entry = file_proto.message_type.add()
    metadata_entry.name = "TaskMetadataEntry"

    field = metadata_entry.field.add()
    field.name = "key"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field = metadata_entry.field.add()
    field.name = "value"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # Task message definition
    task_msg = file_proto.message_type.add()
    task_msg.name = "Task"

    fields = [
        ("id", 1, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        ("type", 2, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        ("payload", 3, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        ("metadata", 4, descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE),
        ("status", 5, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        ("created_at", 6, descriptor_pb2.FieldDescriptorProto.TYPE_INT64),
        ("updated_at", 7, descriptor_pb2.FieldDescriptorProto.TYPE_INT64),
        ("result", 8, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        ("worker_id", 9, descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
    ]

    for name, number, field_type in fields:
        field = task_msg.field.add()
        field.name = name
        field.number = number
        field.label = (
            descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
            if name == "metadata"
            else descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
        )
        field.type = field_type
        if name == "metadata":
            field.type_name = ".nova.taskqueue.TaskMetadataEntry"

    # EnqueueRequest message
    enqueue_request = file_proto.message_type.add()
    enqueue_request.name = "EnqueueRequest"

    field = enqueue_request.field.add()
    field.name = "type"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field = enqueue_request.field.add()
    field.name = "payload"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field = enqueue_request.field.add()
    field.name = "metadata"
    field.number = 3
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".nova.taskqueue.TaskMetadataEntry"

    # EnqueueResponse message
    enqueue_response = file_proto.message_type.add()
    enqueue_response.name = "EnqueueResponse"

    field = enqueue_response.field.add()
    field.name = "task"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".nova.taskqueue.Task"

    # DequeueRequest message
    dequeue_request = file_proto.message_type.add()
    dequeue_request.name = "DequeueRequest"

    field = dequeue_request.field.add()
    field.name = "worker_id"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # DequeueResponse message
    dequeue_response = file_proto.message_type.add()
    dequeue_response.name = "DequeueResponse"

    field = dequeue_response.field.add()
    field.name = "has_task"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL

    field = dequeue_response.field.add()
    field.name = "task"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".nova.taskqueue.Task"

    # AckRequest message
    ack_request = file_proto.message_type.add()
    ack_request.name = "AckRequest"

    field = ack_request.field.add()
    field.name = "task_id"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field = ack_request.field.add()
    field.name = "success"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL

    field = ack_request.field.add()
    field.name = "result"
    field.number = 3
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # AckResponse message
    ack_response = file_proto.message_type.add()
    ack_response.name = "AckResponse"

    field = ack_response.field.add()
    field.name = "task"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".nova.taskqueue.Task"

    # ListTasksRequest message
    list_request = file_proto.message_type.add()
    list_request.name = "ListTasksRequest"

    field = list_request.field.add()
    field.name = "status"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # ListTasksResponse message
    list_response = file_proto.message_type.add()
    list_response.name = "ListTasksResponse"

    field = list_response.field.add()
    field.name = "tasks"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".nova.taskqueue.Task"

    # Service definition
    service = file_proto.service.add()
    service.name = "TaskQueue"

    def _add_rpc(name: str, input_type: str, output_type: str) -> None:
        method = service.method.add()
        method.name = name
        method.input_type = input_type
        method.output_type = output_type
    _add_rpc("Enqueue", ".nova.taskqueue.EnqueueRequest", ".nova.taskqueue.EnqueueResponse")
    _add_rpc("Dequeue", ".nova.taskqueue.DequeueRequest", ".nova.taskqueue.DequeueResponse")
    _add_rpc("Ack", ".nova.taskqueue.AckRequest", ".nova.taskqueue.AckResponse")
    _add_rpc("ListTasks", ".nova.taskqueue.ListTasksRequest", ".nova.taskqueue.ListTasksResponse")

    return file_proto


_POOL = descriptor_pool.Default()
_FILE_DESCRIPTOR = _POOL.Add(_build_file_descriptor())
_SYM_DB = _symbol_database.Default()


def _build_message_class(name: str) -> type:
    descriptor = _FILE_DESCRIPTOR.message_types_by_name[name]
    cls = _reflection.GeneratedProtocolMessageType(
        descriptor.name,
        (_message.Message,),
        {"DESCRIPTOR": descriptor, "__module__": __name__},
    )
    _SYM_DB.RegisterMessage(cls)
    return cls


Task = _build_message_class("Task")
TaskMetadataEntry = _build_message_class("TaskMetadataEntry")
EnqueueRequest = _build_message_class("EnqueueRequest")
EnqueueResponse = _build_message_class("EnqueueResponse")
DequeueRequest = _build_message_class("DequeueRequest")
DequeueResponse = _build_message_class("DequeueResponse")
AckRequest = _build_message_class("AckRequest")
AckResponse = _build_message_class("AckResponse")
ListTasksRequest = _build_message_class("ListTasksRequest")
ListTasksResponse = _build_message_class("ListTasksResponse")

__all__ = [
    "Task",
    "TaskMetadataEntry",
    "EnqueueRequest",
    "EnqueueResponse",
    "DequeueRequest",
    "DequeueResponse",
    "AckRequest",
    "AckResponse",
    "ListTasksRequest",
    "ListTasksResponse",
]
