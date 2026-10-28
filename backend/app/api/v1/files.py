"""AI Sentinel — /files endpoints: upload pdf/word/image/audio."""
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import UserFile
from app.schemas import FileOut

router = APIRouter(prefix="/files", tags=["research"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/x-m4a": "audio",
    "audio/mp4": "audio",
    "text/markdown": "md",
    "text/plain": "md",
}


@router.post("", response_model=FileOut)
def upload_file(file: UploadFile, db: Session = Depends(get_db)) -> FileOut:
    """Upload a file (pdf/docx/image/audio). Processing runs in the pipeline."""
    ftype = ALLOWED.get(file.content_type or "")
    if ftype is None:
        raise HTTPException(415, f"unsupported file type: {file.content_type}")

    dest = UPLOAD_DIR / (f"{file.filename or 'upload'}")
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    row = UserFile(
        filename=file.filename or dest.name,
        file_type=ftype,
        stored_path=str(dest),
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    from app.pipeline.file_processing import process_user_file  # local import: heavy deps

    process_user_file(row.id)
    db.refresh(row)
    return FileOut.model_validate(row)


@router.get("/{file_id}", response_model=FileOut)
def file_status(file_id: int, db: Session = Depends(get_db)) -> FileOut:
    row = db.get(UserFile, file_id)
    if row is None:
        raise HTTPException(404, "file not found")
    return FileOut.model_validate(row)
