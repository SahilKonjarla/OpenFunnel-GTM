from fastapi import APIRouter
from core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/ping")
def ping():
    logger.info("Received ping", extra={"event": "ping"})
    return {"status": "ok"}