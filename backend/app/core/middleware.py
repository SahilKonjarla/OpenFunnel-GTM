from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response

from ..core.logging import get_logger
from ..core.request_context import clear_request_id, set_request_id

logger = get_logger("api_middleware")

async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    request_id = str(uuid.uuid4())
    set_request_id(request_id)

    start = time.perf_counter()
    logger.info(
        "request_start",
        extra={
            "event": "api.request_start",
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception(
            "request_error",
            extra={"event": "api.request_error", "method": request.method, "path": request.url.path},
        )
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)

        # if the response exists, attach the header
        logger.info(
            "request_end",
            extra={
                "event": "api.request_end",
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        clear_request_id()
