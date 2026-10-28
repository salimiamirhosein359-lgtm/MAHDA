"""AI Sentinel — /chat endpoints: lightweight in-RAM chat history.

History is kept in a module-level dict (no database). It survives for the
process lifetime and is lost on restart — by design, since no schema changes
are allowed. ``POST /api/v1/ask`` records each turn here automatically.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Query

router = APIRouter(prefix="/chat", tags=["chat"])

# ---- in-RAM store (thread-safe) ----
_LOCK = threading.Lock()
_HISTORY: list[dict] = []
_MAX_TURNS = 200  # cap memory usage


def record_turn(question: str, result: dict) -> dict:
    """Record one chat turn: question + answer + source count. Best-effort."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": result.get("answer", ""),
        "online": bool(result.get("online", False)),
        "n_sources": len(result.get("sources", [])),
    }
    with _LOCK:
        _HISTORY.append(entry)
        if len(_HISTORY) > _MAX_TURNS:
            del _HISTORY[:-_MAX_TURNS]
    return entry


def _snapshot() -> list[dict]:
    with _LOCK:
        return [dict(e) for e in _HISTORY]


@router.get("/history")
def get_history(
    limit: int = Query(default=50, ge=1, le=_MAX_TURNS),
) -> dict:
    """Return recent chat turns, newest last. RAM-only (lost on restart)."""
    items = _snapshot()
    if limit and len(items) > limit:
        items = items[-limit:]
    return {"count": len(items), "turns": items}


@router.delete("/history")
def clear_history() -> dict:
    """Clear the in-RAM chat history."""
    with _LOCK:
        n = len(_HISTORY)
        _HISTORY.clear()
    return {"cleared": n}
