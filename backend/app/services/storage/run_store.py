from __future__ import annotations
from datetime import datetime as dt
from sqlalchemy.orm import Session
from app.db.models import Run

def create_run(db: Session, *, source: str, status: str = "running", notes: str | None = None) -> Run:
    run = Run(source=source, status=status, notes=notes, created_at=dt.utcnow())
    db.add(run)
    db.flush()
    return run

def mark_run_done(db: Session, *, run_id, status: str) -> None:
    run = db.get(Run, run_id)
    if run:
        run.status = status
        db.flush()
