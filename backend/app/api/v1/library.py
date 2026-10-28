"""AI Sentinel — /library endpoints: personal library."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LibraryEntry
from app.schemas import LibraryIn, LibraryOut

router = APIRouter(prefix="/library", tags=["research"])


@router.get("", response_model=list[LibraryOut])
def list_library(db: Session = Depends(get_db)) -> list[LibraryOut]:
    rows = db.execute(select(LibraryEntry).order_by(LibraryEntry.id.desc())).scalars().all()
    return [LibraryOut.model_validate(e) for e in rows]


@router.post("", response_model=LibraryOut)
def add_to_library(payload: LibraryIn, db: Session = Depends(get_db)) -> LibraryOut:
    if payload.item_id is None and payload.user_file_id is None:
        raise HTTPException(422, "item_id or user_file_id required")
    row = LibraryEntry(
        item_id=payload.item_id,
        user_file_id=payload.user_file_id,
        title=payload.title,
        note=payload.note,
        tags=payload.tags,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LibraryOut.model_validate(row)


@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(LibraryEntry, entry_id)
    if row is not None:
        db.delete(row)
        db.commit()
    return {"ok": True}
