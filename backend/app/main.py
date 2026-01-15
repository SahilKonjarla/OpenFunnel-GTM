from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import init_logging
from app.api.routes import health, jobs, ingest

init_logging("api")

app = FastAPI(title="OpenFunnel-GTM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
