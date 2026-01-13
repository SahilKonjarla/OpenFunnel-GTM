from fastapi import FastAPI, Request
from app.core.logging import init_logging
from app.api.routes.health import health_router
from app.api.routes.orchestrate import orchestrate_router
from app.core.middleware import request_id_middleware

# Initialize logging
init_logging("api")

app = FastAPI(title="OpenFunnel API", version="0.1.0")

app.middleware("http")(request_id_middleware)

# Register the routers
app.include_router(orchestrate_router)
app.include_router(health_router)