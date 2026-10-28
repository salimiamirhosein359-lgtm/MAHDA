"""AI Sentinel — /ask endpoints: RAG (memory) + online Perplexity-style Q&A."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AskIn, AskOut
from app.research.rag import answer_question

router = APIRouter(prefix="/ask", tags=["research"])


@router.post("", response_model=AskOut)
def ask(payload: AskIn, db: Session = Depends(get_db)) -> AskOut:
    """Ask a question.

    online=False → answers from the internal monitored memory (RAG).
    online=True  → live web search too, Perplexity-style numbered citations.
    """
    return answer_question(db, payload.question, online=payload.online)
