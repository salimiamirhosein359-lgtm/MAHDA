"""AI Sentinel — RAG + online Q&A (Perplexity-style with numbered citations)."""
import logging

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.llm.llm import llm_complete
from app.models import Item
from app.research.web_search import web_search

log = logging.getLogger("ai_sentinel.rag")


def _memory_context(db: Session, question: str, k: int = 6) -> list[dict]:
    """Vector search over monitored items (pgvector cosine). Falls back to keyword match."""
    try:
        from app.llm.embeddings import embed

        qvec = embed(question)
        if qvec:
            rows = db.execute(
                sql_text(
                    "SELECT id, title, url, summary, embedding <=> :qvec AS dist "
                    "FROM items WHERE ai_relevant = true AND embedding IS NOT NULL "
                    "ORDER BY dist LIMIT :k"
                ),
                {"qvec": str(qvec), "k": k},
            ).fetchall()
            if rows:
                return [{"title": r[1], "url": r[2], "snippet": (r[3] or "")[:300]} for r in rows]
    except Exception as e:
        log.warning("vector search failed, falling back to keywords: %s", e)

    # fallback: simple parameterized keyword search
    words = [w for w in question.split() if len(w) > 3][:5]
    if not words:
        return []
    rows = db.execute(
        sql_text(
            "SELECT id, title, url, summary FROM items WHERE ai_relevant = true AND ("
            + " OR ".join(["summary ILIKE :w%d" % i for i in range(len(words))])
            + ") LIMIT :k"
        ),
        {**{f"w{i}": f"%{w}%" for i, w in enumerate(words)}, "k": k},
    ).fetchall()
    return [{"title": r[1], "url": r[2], "snippet": (r[3] or "")[:300]} for r in rows]


ASK_SYSTEM = """You are a Persian-speaking AI research assistant. Answer the question using
ONLY the provided sources. Cite them inline with numbered references like [1], [2] — exactly
like Perplexity. If the sources are insufficient, say so explicitly. Answer in Persian unless
the question is in English. Be factual and concise."""


def answer_question(db: Session, question: str, online: bool = False):
    """Answer from internal memory (RAG) and optionally live web. Perplexity-style citations."""
    from app.schemas import AskOut, AskSourceOut

    memory = _memory_context(db, question)
    web = web_search(question) if online else []

    # numbered sources: memory first, then web
    sources: list[AskSourceOut] = []
    for i, s in enumerate(memory + web, start=1):
        sources.append(AskSourceOut(ref_no=i, title=s["title"], url=s["url"], snippet=s.get("snippet")))

    if not sources:
        return AskOut(
            answer="منبعی برای پاسخ به این سؤال پیدا نشد. ابتدا کالکتورها را اجرا کنید تا حافظه بسازد"
                   + (" یا اتصال اینترنت/موتور جستجو را بررسی کنید." if online else "."),
            sources=[],
            online=online,
        )

    context = "\n\n".join(f"[{s.ref_no}] {s.title}\nURL: {s.url}\n{s.snippet or ''}" for s in sources)
    prompt = f"Question: {question}\n\nSources:\n{context}\n\nAnswer (with [n] citations):"
    answer = llm_complete(prompt, system=ASK_SYSTEM)

    return AskOut(answer=answer, sources=sources, online=online)
