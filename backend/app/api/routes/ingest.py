from fastapi import APIRouter
from pydantic import BaseModel
from app.db.redis_client import get_redis
from app.queue.redis_queue import enqueue

router = APIRouter()

class SeedRequest(BaseModel):
    companies: list[str]

@router.post("/seed-greenhouse")
def seed_greenhouse(req: SeedRequest):
    r = get_redis()
    for c in req.companies:
        enqueue(r, "discover", {"source": "greenhouse", "company": c})
    return {"enqueued": len(req.companies)}
