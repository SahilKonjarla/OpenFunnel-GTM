from fastapi import FastAPI
from app.core.logging import init_logging
from app.api.routes.health import health_router
from app.api.routes.job_postings import router as job_router
from app.api.routes.orchestrate import orchestrate_router
from app.core.middleware import request_id_middleware
from app.core.config import settings

# Initialize logging
init_logging("api")

app = FastAPI(title="OpenFunnel API", version="0.1.0")

app.middleware("http")(request_id_middleware)

# Register the routers
app.include_router(orchestrate_router)
app.include_router(health_router)
app.include_router(job_router)
if settings.app_env == "dev":
    from app.api.routes.debug_seed import debug_router
    from app.api.routes.debug_queue import debug_queue_router
    app.include_router(debug_queue_router)
    app.include_router(debug_router)