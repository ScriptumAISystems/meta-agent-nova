"""Redis-backed task repository tests."""
from __future__ import annotations

import threading
import time

import pytest

from nova.task_queue import RedisTaskRepository
from nova.task_queue.redis_storage import InMemoryRedis


@pytest.fixture()
def redis_repository() -> RedisTaskRepository:
    client = InMemoryRedis()
    repository = RedisTaskRepository(client)
    yield repository
    client.close()


def test_redis_enqueue_dequeue_ack(redis_repository: RedisTaskRepository) -> None:
    record = redis_repository.enqueue("demo", "payload", {"priority": "high"})
    assert record.status == "PENDING"

    dequeued = redis_repository.dequeue("worker-1")
    assert dequeued is not None
    assert dequeued.worker_id == "worker-1"
    assert dequeued.attempts == 1

    acked = redis_repository.ack(dequeued.id, True, "done")
    assert acked.status == "COMPLETED"
    assert acked.result == "done"

    listed = redis_repository.list_tasks()
    assert len(listed) == 1
    assert listed[0].status == "COMPLETED"


def test_redis_recover_overdue_tasks(redis_repository: RedisTaskRepository) -> None:
    record = redis_repository.enqueue("demo", "payload")
    dequeued = redis_repository.dequeue("worker-1")
    assert dequeued is not None
    assert dequeued.attempts == 1

    requeued, failed = redis_repository.recover_overdue_tasks(-1, max_attempts=3)
    assert failed == []
    assert len(requeued) == 1
    assert requeued[0].id == record.id
    assert requeued[0].status == "PENDING"
    assert requeued[0].worker_id is None

    redis_repository.dequeue("worker-2")
    _, failed_final = redis_repository.recover_overdue_tasks(-1, max_attempts=2)
    assert len(failed_final) == 1
    assert failed_final[0].status == "FAILED"
    assert failed_final[0].result == "maximum attempts exceeded"


def test_redis_heartbeat_updates_timestamp(redis_repository: RedisTaskRepository) -> None:
    redis_repository.enqueue("demo", "payload")
    claimed = redis_repository.dequeue("worker-1")
    assert claimed is not None
    original_update = claimed.updated_at

    time.sleep(0.01)
    redis_repository.heartbeat(claimed.id)
    refreshed = redis_repository.list_tasks("IN_PROGRESS")[0]
    assert refreshed.updated_at >= original_update


def test_redis_concurrency_with_latency_injection() -> None:
    client = InMemoryRedis(latency_ms=1.5)
    repository = RedisTaskRepository(client)

    total_jobs = 1000
    for index in range(total_jobs):
        repository.enqueue("bulk", f"payload-{index}")

    completed_ids: set[str] = set()
    completed_lock = threading.Lock()
    done_event = threading.Event()

    def worker(worker_index: int) -> None:
        worker_id = f"worker-{worker_index}"
        while True:
            record = repository.dequeue(worker_id)
            if record is None:
                if done_event.is_set():
                    break
                time.sleep(0.002)
                continue
            acked = repository.ack(record.id, True, "ok")
            assert acked.status == "COMPLETED"
            with completed_lock:
                completed_ids.add(acked.id)
                if len(completed_ids) == total_jobs:
                    done_event.set()

    workers = [threading.Thread(target=worker, args=(idx,), daemon=True) for idx in range(10)]
    for thread in workers:
        thread.start()
    for thread in workers:
        thread.join()

    assert len(completed_ids) == total_jobs

    completed = repository.list_tasks("COMPLETED")
    assert len(completed) == total_jobs

    client.close()
