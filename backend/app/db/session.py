from __future__ import annotations
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import redis
from app.core.config import settings

# Set up postgres connection
engine = create_engine(settings.postgres_dsn, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def db_healthcheck() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

# Set up redis connection
redis_client = redis.Redis.from_url(settings.redis_url)

def get_redis() -> redis.Redis:
    return redis_client

def redis_healthcheck() -> bool:
    try:
        redis_client.ping()
        return True
    except Exception:
        return False
