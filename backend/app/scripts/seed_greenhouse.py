from __future__ import annotations
import datetime as dt
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Run
from app.db.redis_client import get_redis
from app.queue.redis_queue import enqueue
from importlib.resources import files

SEED_FILE = files("app.seed").joinpath("greenhouse_companies.txt")

def main():
    companies = [l.strip() for l in SEED_FILE.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.strip().startswith("#")]
    r = get_redis()
    db: Session = SessionLocal()
    run = Run(note=f"seed {dt.datetime.now().isoformat()} companies={len(companies)}")
    db.add(run); db.commit()
    for c in companies:
        enqueue(r, "discover", {"source": "greenhouse", "company": c, "run_id": str(run.id)})
    print(f"enqueued {len(companies)} discovery tasks")
    db.close()

if __name__ == "__main__":
    main()
