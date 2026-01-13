from fastapi import APIRouter, status, HTTPException
from app.core.logging import get_logger
from app.db.session import db_healthcheck, redis_healthcheck

health_router = APIRouter()
logger = get_logger(__name__)

@health_router.get("/health", tags=["health"])
def health():
    pg_ok = db_healthcheck()
    redis_ok = redis_healthcheck()

    if pg_ok and redis_ok:
        logger.info("health_ok", extra={"event": "api.health_ok"})
        return {"status": "ok", "postgres": True, "redis": True}

    logger.warning(
        "health_fail",
        extra={
            "event": "api.health_fail",
            "postgres": pg_ok,
            "redis": redis_ok,
        },
    )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"status": "error", "postgres": pg_ok, "redis": redis_ok},
    )

@health_router.get("/ping", tags=["health"])
def ping():
    logger.info("ping", extra={"event": "api.ping"})
    return {"status": "ok"}
