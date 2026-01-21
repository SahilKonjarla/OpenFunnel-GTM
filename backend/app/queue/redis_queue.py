import json
import time
import uuid
from dataclasses import dataclass
from typing import Any
from redis import Redis

@dataclass
class Task:
    # Unique task identifier (UUID string).
    id: str
    # Logical queue / worker type (e.g. "discover", "scrape", "extract").
    type: str
    # Arbitrary JSON-serializable payload for the worker.
    payload: dict[str, Any]
    # How many times this task has been retried (incremented on failure).
    attempts: int = 0


def _now() -> float:
    # Current UNIX time in seconds.
    # Kept as a function to make testing/mocking easier.
    return time.time()


def enqueue(r: Redis, task_type: str, payload: dict[str, Any]) -> str:
    # Create a new task with a unique id.
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "type": task_type,
        "payload": payload,
        "attempts": 0,
    }

    # Push onto the left side of the list queue.
    # Consumers use rpop (right-pop), giving FIFO-ish behavior.
    r.lpush(f"q:{task_type}", json.dumps(task))

    return task_id


def lease_batch(
    r: Redis,
    task_type: str,
    batch_size: int,
    visibility_timeout_sec: int,
) -> list[Task]:
    # Lease up to `batch_size` tasks from the main queue and move them into
    # a "processing" sorted set with a deadline score (visibility timeout).
    # If a worker crashes after leasing but before ack'ing, the reaper can
    # requeue tasks whose deadlines have passed.
    tasks: list[Task] = []

    qkey = f"q:{task_type}"  # main queue list
    pkey = f"p:{task_type}"  # processing ZSET: member=raw json, score=deadline

    deadline = _now() + visibility_timeout_sec

    for _ in range(batch_size):
        raw = r.rpop(qkey)
        if raw is None:
            break

        # Record the leased item with its deadline.
        r.zadd(pkey, {raw: deadline})

        # Parse into a structured Task for the worker.
        d = json.loads(raw)
        tasks.append(Task(**d))

    return tasks

def ack(r: Redis, task_type: str, task: Task) -> None:
    # Acknowledge successful processing by removing the task from processing set.
    pkey = f"p:{task_type}"

    raw = json.dumps(
        {
            "id": task.id,
            "type": task.type,
            "payload": task.payload,
            "attempts": task.attempts,
        }
    )

    r.zrem(pkey, raw)

def fail_and_maybe_requeue(
    r: Redis,
    task_type: str,
    task: Task,
    max_attempts: int = 5,
) -> None:
    # Handle a failed task:
    # - Remove from processing set
    # - Increment attempts
    # - If attempts exceed threshold -> send to DLQ
    # - Otherwise requeue for retry
    pkey = f"p:{task_type}"

    raw = json.dumps(
        {
            "id": task.id,
            "type": task.type,
            "payload": task.payload,
            "attempts": task.attempts,
        }
    )
    r.zrem(pkey, raw)

    task.attempts += 1

    if task.attempts >= max_attempts:
        # Dead-letter queue for tasks that exceeded retry budget.
        r.lpush(f"dlq:{task_type}", json.dumps(task.__dict__))
        return

    # Put it back on the main queue for another attempt.
    r.lpush(f"q:{task_type}", json.dumps(task.__dict__))


def requeue_stale(
    r: Redis,
    task_type: str,
    visibility_timeout_sec: int,
    max_to_requeue: int = 100,
) -> int:
    # Requeue tasks whose visibility timeout has expired.
    #
    # The "processing" ZSET stores members with score=deadline timestamp.
    # Any tasks with score <= now are considered stale and will be moved back
    # to the main queue.
    #
    # Args:
    #   visibility_timeout_sec: included for interface symmetry / callers, but
    #   the deadlines were already computed at lease-time. The effective timeout
    #   is the one used in lease_batch.
    pkey = f"p:{task_type}"
    qkey = f"q:{task_type}"

    now = _now()

    # Fetch up to max_to_requeue expired members.
    stale = r.zrangebyscore(pkey, 0, now, start=0, num=max_to_requeue)
    if not stale:
        return 0

    # Pipeline to reduce round trips and make the move faster.
    pipe = r.pipeline()
    for raw in stale:
        pipe.zrem(pkey, raw)
        pipe.lpush(qkey, raw)
    pipe.execute()

    return len(stale)
