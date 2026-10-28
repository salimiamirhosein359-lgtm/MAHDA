"""AI Sentinel — /bulletins endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bulletin
from app.schemas import BulletinOut

router = APIRouter(prefix="/bulletins", tags=["radar"])


@router.get("", response_model=list[BulletinOut])
def list_bulletins(limit: int = 10, db: Session = Depends(get_db)) -> list[BulletinOut]:
    rows = db.execute(select(Bulletin).order_by(Bulletin.id.desc()).limit(limit)).scalars().all()
    return [BulletinOut.model_validate(b) for b in rows]
