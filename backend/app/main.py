from fastapi import FastAPI, Request
from core.logging import init_logging, get_logger
from core.request_context import set_request_id, clear_request_id
from api.routes.health import health_router
from api.routes.orchestrate import orchestrate_router
import uuid

# Initialize logging
init_logging("api")

app = FastAPI(title="OpenFunnel API", version="0.1.0")

# Register the middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    set_request_id(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    clear_request_id()
    return response

# Register the routers
app.include_router(orchestrate_router)
app.include_router(health_router)