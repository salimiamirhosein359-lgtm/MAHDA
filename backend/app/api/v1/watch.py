"""AI Sentinel — /watch endpoints: tracked topics/people/companies."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WatchTopic
from app.schemas import WatchIn, WatchOut

router = APIRouter(prefix="/watch", tags=["radar"])


@router.get("", response_model=list[WatchOut])
def list_watch(db: Session = Depends(get_db)) -> list[WatchOut]:
    rows = db.execute(select(WatchTopic)).scalars().all()
    return [WatchOut.model_validate(w) for w in rows]


@router.post("", response_model=WatchOut)
def add_watch(payload: WatchIn, db: Session = Depends(get_db)) -> WatchOut:
    row = WatchTopic(term=payload.term, kind=payload.kind)
    db.add(row)
    db.commit()
    db.refresh(row)
    return WatchOut.model_validate(row)


@router.delete("/{watch_id}")
def delete_watch(watch_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(WatchTopic, watch_id)
    if row is not None:
        db.delete(row)
        db.commit()
    return {"ok": True}
