"""AI Sentinel — /items endpoints: live feed of monitored items."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.schemas import ItemListOut, ItemOut

router = APIRouter(prefix="/items", tags=["radar"])


@router.get("", response_model=ItemListOut)
def list_items(
    category: str | None = None,
    camp: str | None = None,
    item_type: str | None = None,
    source_id: int | None = None,
    min_score: float | None = None,
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> ItemListOut:
    """List monitored items with filters (category, camp, score, time)."""
    q = select(Item).where(Item.ai_relevant.is_(True))

    if category:
        q = q.where(Item.category == category)
    if camp:
        q = q.where(Item.camp == camp)
    if item_type:
        q = q.where(Item.item_type == item_type)
    if source_id:
        q = q.where(Item.source_id == source_id)
    if min_score is not None:
        q = q.where(Item.score >= min_score)
    if days:
        since = datetime.utcnow() - timedelta(days=days)
        q = q.where(Item.created_at >= since)

    total = db.scalar(
        select(func.count()).select_from(q.subquery())
    )
    rows = db.execute(
        q.order_by(Item.published_at.desc().nullslast(), Item.score.desc().nullslast())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return ItemListOut(total=total or 0, items=[ItemOut.model_validate(r) for r in rows])


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemOut:
    row = db.get(Item, item_id)
    if row is None:
        raise HTTPException(404, "item not found")
    return ItemOut.model_validate(row)
