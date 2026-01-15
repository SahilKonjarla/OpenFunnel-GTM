import json, time, uuid
from dataclasses import dataclass
from typing import Any
from redis import Redis

@dataclass
class Task:
    id: str
    type: str
    payload: dict[str, Any]
    attempts: int = 0

def _now() -> float:
    return time.time()

def enqueue(r: Redis, task_type: str, payload: dict[str, Any]) -> str:
    task_id = str(uuid.uuid4())
    task = {"id": task_id, "type": task_type, "payload": payload, "attempts": 0}
    r.lpush(f"q:{task_type}", json.dumps(task))
    return task_id

def lease_batch(r: Redis, task_type: str, batch_size: int, visibility_timeout_sec: int) -> list[Task]:
    tasks: list[Task] = []
    qkey = f"q:{task_type}"
    pkey = f"p:{task_type}"
    deadline = _now() + visibility_timeout_sec
    for _ in range(batch_size):
        raw = r.rpop(qkey)
        if raw is None:
            break
        r.zadd(pkey, {raw: deadline})
        d = json.loads(raw)
        tasks.append(Task(**d))
    return tasks

def ack(r: Redis, task_type: str, task: Task) -> None:
    pkey = f"p:{task_type}"
    raw = json.dumps({"id": task.id, "type": task.type, "payload": task.payload, "attempts": task.attempts})
    r.zrem(pkey, raw)

def fail_and_maybe_requeue(r: Redis, task_type: str, task: Task, max_attempts: int = 5) -> None:
    pkey = f"p:{task_type}"
    raw = json.dumps({"id": task.id, "type": task.type, "payload": task.payload, "attempts": task.attempts})
    r.zrem(pkey, raw)
    task.attempts += 1
    if task.attempts >= max_attempts:
        r.lpush(f"dlq:{task_type}", json.dumps(task.__dict__))
        return
    r.lpush(f"q:{task_type}", json.dumps(task.__dict__))

def requeue_stale(r: Redis, task_type: str, visibility_timeout_sec: int, max_to_requeue: int = 100) -> int:
    pkey = f"p:{task_type}"
    qkey = f"q:{task_type}"
    now = _now()
    stale = r.zrangebyscore(pkey, 0, now, start=0, num=max_to_requeue)
    if not stale:
        return 0
    pipe = r.pipeline()
    for raw in stale:
        pipe.zrem(pkey, raw)
        pipe.lpush(qkey, raw)
    pipe.execute()
    return len(stale)
