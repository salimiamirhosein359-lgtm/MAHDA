"""AI Sentinel — /alerts endpoints (dashboard alerts, phase 1)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Alert
from app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["radar"])


@router.get("", response_model=list[AlertOut])
def list_alerts(only_unseen: bool = False, limit: int = 50, db: Session = Depends(get_db)) -> list[AlertOut]:
    q = select(Alert).order_by(Alert.id.desc()).limit(limit)
    if only_unseen:
        q = q.where(Alert.seen.is_(False))
    rows = db.execute(q).scalars().all()
    return [AlertOut.model_validate(a) for a in rows]


@router.post("/{alert_id}/seen")
def mark_seen(alert_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(Alert, alert_id)
    if row is None:
        return {"ok": False}
    row.seen = True
    db.commit()
    return {"ok": True}
