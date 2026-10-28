"""AI Sentinel — /trends endpoint: hot topics per category."""
import re
from datetime import datetime, timedelta
from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Item
from app.pipeline.rules import strip_html
from app.schemas import TrendOut

router = APIRouter(prefix="/trends", tags=["radar"])

# Simple stopword list (en) — hot keywords come from titles/summaries.
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "at", "by",
    "from", "is", "are", "was", "were", "be", "been", "new", "how", "why", "what",
    "this", "that", "it", "its", "as", "ai", "says", "will", "can", "us", "about",
    # HTML / feed junk that leaks into RSS summaries
    "wp-", "alt", "src", "href", "http", "https", "www", "com", "class", "width",
    "height", "size", "attachment", "figure", "img", "figcaption", "8230", "read",
    "more", "continue", "rss", "feed", "getty", "bloomberg",
}

# Reject leftover HTML-ish tokens: start with "<", end with ">", contain "="
# or a double-quote, or contain "http".
_JUNK_RE = re.compile(r"(^<|>$|=|\"|http)")

# Punctuation stripped from word edges (incl. unicode: … — – «»)
_TRIM_CHARS = ".,:;!?()[]{}\"'«»…—–"


def _keywords(text: str) -> list[str]:
    # strip HTML first: RSS summaries leak <figure><img ...> etc.
    clean = strip_html(text)
    words = [w.strip(_TRIM_CHARS).lower() for w in clean.split()]
    return [
        w for w in words
        if len(w) > 3 and w not in _STOP and not _JUNK_RE.search(w)
    ]


@router.get("", response_model=list[TrendOut])
def trends(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TrendOut]:
    """Hot keywords per category: count + momentum (recent vs previous period)."""
    since = datetime.utcnow() - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    recent = db.execute(
        select(Item).where(Item.ai_relevant.is_(True), Item.created_at >= since)
    ).scalars().all()
    previous = db.execute(
        select(Item).where(
            Item.ai_relevant.is_(True), Item.created_at >= prev_since, Item.created_at < since
        )
    ).scalars().all()

    now_counter: Counter = Counter()
    prev_counter: Counter = Counter()
    cat_of: dict[str, str | None] = {}

    for it in recent:
        for kw in _keywords(f"{it.title} {it.summary or ''}"):
            now_counter[kw] += 1
            cat_of.setdefault(kw, it.category)
    for it in previous:
        for kw in _keywords(f"{it.title} {it.summary or ''}"):
            prev_counter[kw] += 1

    out: list[TrendOut] = []
    for kw, count in now_counter.most_common(limit):
        momentum = (count - prev_counter.get(kw, 0)) / max(prev_counter.get(kw, 1), 1)
        out.append(TrendOut(category=cat_of.get(kw), keyword=kw, count=count, momentum=round(momentum, 2)))
    return out
