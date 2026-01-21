from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(settings.postgres_dsn, pool_pre_ping=True)

# Factory that creates new SQLAlchemy Session objects.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # The session is always closed after the request finishes.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
