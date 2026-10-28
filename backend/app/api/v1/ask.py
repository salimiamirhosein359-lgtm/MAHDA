"""AI Sentinel — /ask endpoints: chatbot retrieval (archive + web, LLM-optional)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import AskIn, AskOut, AskSourceOut
from app.research.chat import chat_retrieve
from app.api.v1.chat import record_turn

router = APIRouter(prefix="/ask", tags=["research"])


@router.post("", response_model=AskOut)
def ask(payload: AskIn, db: Session = Depends(get_db)) -> AskOut:
    """Ask the chatbot a question.

    online=False → answers from the internal monitored archive only.
    online=True  → live web search too (SearXNG), merged + ranked.
    The answer is composed structurally (no cloud LLM key required);
    if an LLM is configured, its answer is layered on top.
    """
    result = chat_retrieve(payload.question, online=payload.online, db=db)

    # keep a lightweight RAM history for the chat UI (best-effort)
    try:
        record_turn(payload.question, result)
    except Exception:
        pass

    sources = [
        AskSourceOut(
            ref_no=s["ref_no"],
            title=s.get("title", ""),
            url=s.get("url", ""),
            snippet=s.get("snippet"),
        )
        for s in result["sources"]
    ]
    return AskOut(answer=result["answer"], sources=sources, online=result["online"])
