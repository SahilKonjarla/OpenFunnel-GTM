from fastapi import FastAPI
from api.routes.health import health_router

app = FastAPI()

app.include_router(health_router)