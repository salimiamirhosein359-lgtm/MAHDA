"""AI Sentinel — /rivalry endpoint: China-US AI rivalry dashboard."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import CampStat, ItemOut, RivalryOut

router = APIRouter(prefix="/rivalry", tags=["radar"])


def _camp_stat(db: Session, camp: str, days: int, limit: int) -> CampStat:
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.execute(
        select(Item)
        .where(Item.camp == camp, Item.ai_relevant.is_(True), Item.created_at >= since)
        .order_by(Item.score.desc().nullslast())
        .limit(limit)
    ).scalars().all()
    return CampStat(camp=camp, count=len(rows), top_items=[ItemOut.model_validate(r) for r in rows])


@router.get("", response_model=RivalryOut)
def rivalry(
    days: int = Query(default=7, ge=1, le=90),
    top: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RivalryOut:
    """Two-column view: US ecosystem vs CN ecosystem (eagle view 🦅)."""
    return RivalryOut(
        since=datetime.utcnow() - timedelta(days=days),
        us=_camp_stat(db, "US", days, top),
        cn=_camp_stat(db, "CN", days, top),
    )
