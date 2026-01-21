from fastapi import APIRouter

# FastAPI router for grouping related endpoints.
router = APIRouter()

@router.get("/healthz")
def healthz() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: A simple JSON response indicating the server is running.
    """
    return {"ok": True}
