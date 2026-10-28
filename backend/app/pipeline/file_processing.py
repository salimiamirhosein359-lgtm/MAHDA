"""AI Sentinel — user file processing: pdf/docx/image/audio → text → embedding."""
import logging
from pathlib import Path

from app.db import SessionLocal
from app.llm.embeddings import embed
from app.models import UserFile

log = logging.getLogger("ai_sentinel.files")


def _extract_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(path: str) -> str:
    import docx

    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs if p.text)


def _extract_image(path: str) -> str:
    """OCR with pytesseract (English + Persian if installed)."""
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(path), lang="eng")


def _transcribe_audio(path: str) -> str:
    from app.config import settings

    if settings.whisper_provider == "local":
        from faster_whisper import WhisperModel

        model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(path)
        return "\n".join(s.text for s in segments)
    # API fallback: whisper via litellm-compatible providers is provider-specific;
    # phase 2 can add an OpenAI whisper call here.
    raise NotImplementedError("api transcription arrives in phase 2")


def process_user_file(file_id: int) -> None:
    """Extract text from the uploaded file, embed it, mark ready. Synchronous (phase 1)."""
    db = SessionLocal()
    try:
        f = db.get(UserFile, file_id)
        if f is None:
            return
        f.status = "processing"
        db.commit()
        try:
            path = Path(f.stored_path)
            if f.file_type == "pdf":
                text = _extract_pdf(str(path))
            elif f.file_type == "docx":
                text = _extract_docx(str(path))
            elif f.file_type == "image":
                text = _extract_image(str(path))
            elif f.file_type == "audio":
                text = _transcribe_audio(str(path))
            elif f.file_type == "md":
                text = path.read_text(encoding="utf-8", errors="ignore")
            else:
                raise ValueError(f"unknown type {f.file_type}")

            f.extracted_text = text[:200000]
            f.embedding = embed(text[:4000]) if text else None
            f.status = "ready"
        except Exception as e:
            log.error("file %s processing failed: %s", file_id, e)
            f.status = "failed"
            f.error = str(e)
        db.commit()
    finally:
        db.close()
