from fastapi import APIRouter
from pydantic import BaseModel
from app.db.redis_client import get_redis
from app.queue.redis_queue import enqueue

# Router for seed-related endpoints (kick off discovery pipelines, etc.)
router = APIRouter()

class SeedRequest(BaseModel):
    # List of company identifiers / names that your discovery worker understands.
    # Example: ["openai", "stripe", "figma"]
    companies: list[str]

@router.post("/seed-greenhouse")
def seed_greenhouse(req: SeedRequest) -> dict:
    # Get a Redis connection/client instance.
    r = get_redis()

    # Enqueue one discovery task per company.
    # Each task will be picked up by the "discover" worker/consumer.
    for c in req.companies:
        enqueue(
            r,
            "discover",
            {
                # Used by your discover worker to decide which scraper/adapter to run.
                "source": "greenhouse",
                # The company to discover jobs for (format depends on your Greenhouse adapter).
                "company": c,
            },
        )

    # Return how many tasks were created.
    return {"enqueued": len(req.companies)}
