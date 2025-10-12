"""gRPC-based task queue for Meta-Agent Nova."""
from .grpc_service import TaskQueueServicer, TaskQueueStub, add_TaskQueueServicer_to_server, task_queue_channel
from .redis_storage import RedisTaskRepository
from .server import TaskQueueServer, TaskQueueService
from .storage import TASK_STATUSES, TaskRecord, TaskRepository
from .vector_ingest import HashingEmbedder, IngestSummary, VectorIngestConfig, VectorIngestor

__all__ = [
    "TaskQueueServer",
    "TaskQueueService",
    "TaskQueueServicer",
    "TaskQueueStub",
    "TaskRepository",
    "RedisTaskRepository",
    "TaskRecord",
    "TASK_STATUSES",
    "HashingEmbedder",
    "IngestSummary",
    "VectorIngestConfig",
    "VectorIngestor",
    "add_TaskQueueServicer_to_server",
    "task_queue_channel",
]
