"""AI Sentinel — scheduler (APScheduler, phase 1) + seed + run helpers.

Run directly:  python -m app.scheduler
"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import settings
from app.db import SessionLocal, engine
from app.logging_setup import setup_logging

log = logging.getLogger("ai_sentinel.scheduler")


def init_db() -> None:
    """Create tables and pgvector extension; seed default sources."""
    from app.models import Base, Source
    from app.collectors.seed_sources import SEED_SOURCES

    # enable pgvector extension if available
    from sqlalchemy import text

    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        except Exception as e:
            log.warning("pgvector extension unavailable (embeddings will use JSON fallback): %s", e)

    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        for s in SEED_SOURCES:
            exists = db.query(Source).filter_by(name=s["name"]).first()
            if not exists:
                db.add(Source(name=s["name"], kind=s["kind"], group=s["group"],
                              camp=s["camp"], weight=s["weight"], config=s["config"]))
        db.commit()
        log.info("seeded sources: %d", len(SEED_SOURCES))
    finally:
        db.close()


def collect_once() -> None:
    from app.pipeline.ingest import run_all_collectors

    results = run_all_collectors()
    log.info("collection finished: %s", results)


def main() -> None:
    setup_logging()
    init_db()

    scheduler = BlockingScheduler()
    scheduler.add_job(collect_once, "interval",
                      minutes=settings.collect_interval_minutes, id="collect")
    log.info("scheduler started (interval=%s min)", settings.collect_interval_minutes)
    collect_once()  # immediate first run
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("scheduler stopped")


if __name__ == "__main__":
    main()
