"""AI Sentinel — chatbot retrieval layer (LLM-optional, RAG-style).

Answers user questions by merging two parallel sources:
1. Internal archive (PostgreSQL ``items``) — keyword match on title/summary
   plus category/camp/actor boost and recency.
2. Live web (SearXNG) — via :mod:`app.research.web_search` with a 10s budget.

No cloud LLM key is required: the final answer is *composed* structurally
(overview paragraph → key findings bullets → numbered source list). If an LLM
later becomes available (``llm_complete`` returns non-empty text), its output
is blended in on top of the composed answer.
"""
from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.llm.llm import llm_complete
from app.research.web_search import web_search

log = logging.getLogger("ai_sentinel.chat")

# Web search must never take longer than this many seconds.
WEB_TIMEOUT_SECONDS = 10.0

# ---------------------------------------------------------------------------
# Keyword extraction (Persian + English)
# ---------------------------------------------------------------------------

# English stopwords (question-ish words first, then general noise)
_EN_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "at",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "shall", "may", "might", "must", "new", "how", "why", "what",
    "who", "whom", "whose", "when", "where", "which", "this", "that", "these",
    "those", "it", "its", "as", "us", "about", "tell", "me", "give", "show",
    "latest", "please", "any", "all", "and", "also", "there", "their", "them",
    "they", "he", "she", "his", "her", "we", "you", "your", "my", "our", "i",
}

# Persian stopwords (pronouns, question words, verbs, prepositions)
_FA_STOP = {
    "از", "به", "در", "که", "را", "و", "این", "آن", "است", "هست", "بود",
    "می", "های", "ها", "یک", "تا", "برای", "با", "هم", "نیز", "یا",
    "چه", "چی", "چیست", "چرا", "کجا", "کی", "کدام", "چگونه", "چطور", "چند",
    "خود", "او", "ما", "شما", "من", "بگو", "بده", "نشان", "بدهید",
    "کن", "کند", "کنند", "کنم", "کنیم", "بکن", "شود", "شوند", "شوم",
    "دارد", "دارند", "داشته", "بیان", "گوید", "گویم", "گو",
    "درباره", "حول", "طی", "روی", "زیر", "بین", "وسط", "پس", "چون",
    "اگر", "اما", "ولی", "لی", "همه", "هر", "برخی", "دیگر", "بعضی",
    "جدید", "آخرین", "خبر", "اخبار", "خبرهای", "مورد", "موضوع",
    # verb inflections that whitespace-splitting produces verbatim
    "هستند", "هستم", "هستیم", "هستی", "بودند", "بودم", "بودیم", "بودی",
    "باشد", "باشند", "شده", "شد", "کرد", "کردند", "گردید", "گردیدند",
}

# Persian → English aliases: Persian transliterations of AI companies/terms
# whose archive items are titled in English. Adding the English keyword lets
# a Persian question still hit English archive titles + web results.
# Keys include both ZWNJ (‌) and glued variants.
_FA_ALIAS = {
    "دیپ‌سیک": "deepseek", "دیپسیک": "deepseek", "دیپ": "deepseek",
    "اوپن‌ای‌آی": "openai", "اوپنایآی": "openai", "اوپن‌آی": "openai", "اوپنای‌آی": "openai",
    "گوگل": "google",
    "انویدیا": "nvidia", "اینویدیا": "nvidia", "انویدا": "nvidia",
    "انتروپیک": "anthropic", "آنتراپیک": "anthropic",
    "کلود": "claude",
    "جمینای": "gemini",
    "جی‌پی‌تی": "gpt", "جیپیتی": "gpt",
    "چت‌جی‌پی‌تی": "chatgpt", "چتجیپیتی": "chatgpt",
    "مایکروسافت": "microsoft",
    "آلیبابا": "alibaba", "علی‌بابا": "alibaba",
    "هواوی": "huawei",
    "کوئن": "qwen",
    "مصنوعی": "ai",
    "تراشه": "chip", "تراشه‌ها": "chip",
    "چین": "china",
    "پکن": "beijing", "بیجینگ": "beijing",
    "واشنگتن": "washington", "واشینگتن": "washington",
    # People / CEOs
    "ایلان": "elon musk", "ماسک": "elon musk", "ایلان‌ماسک": "elon musk",
    "سم‌آلتمن": "sam altman", "آلتمن": "sam altman", "سم": "sam altman",
    "جنسن": "jensen huang", "هوانگ": "jensen huang", "جنسن‌هوانگ": "jensen huang",
    "لینگ‌فنگ": "ling feng", "لینگ": "ling feng", "فنگ": "ling feng",
    "ساتیا": "satya nadella", "نادلا": "satya nadella",
    "سوندار": "sundar pichai", "پیچای": "sundar pichai",
    "دمیس": "demis hassabis", "حسابیس": "demis hassabis",
    "داریو": "dario amodei", "آمودی": "dario amodei",
    "لی‌فی‌فی": "li fei-fei", "فی‌فی": "fei-fei li",
    "اندرو": "andrew ng", "انگ": "andrew ng",
    "یان": "yann lecun", "لکان": "yann lecun",
    "رابین": "robin li", "لی‌بین": "robin li",
    "جک": "jack ma", "جک‌ما": "jack ma",
    "رن‌ژنگفی": "ren zhengfei", "ژنگفی": "ren zhengfei",
    # Companies
    "متا": "meta", "فیسبوک": "facebook meta",
    "بایدو": "baidu", "تنسنت": "tencent",
    "شیائومی": "xiaomi",
    "سامسونگ": "samsung",
    "اپل": "apple",
    "آمازون": "amazon", "ای‌دبلیو‌اس": "aws",
    "تسلا": "tesla",
    "اینتل": "intel",
    "ای‌ام‌دی": "amd",
    "کوالکام": "qualcomm",
    "میسترال": "mistral",
    "استیبیلیتی": "stability ai",
    # Terms
    "هوش": "ai", "یادگیری": "machine learning",
    "شبکه‌عصبی": "neural network",
    "ترنسفورمر": "transformer",
    "پردازنده": "processor", "گرافیکی": "gpu",
}

# Persian suffixes stripped when checking stopwords (superlative/plural)
_FA_SUFFIXES = ("ترین", "های", "ها", "تر")


def _is_fa_stop(word: str) -> bool:
    if word in _FA_STOP:
        return True
    for suf in _FA_SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf) + 1:
            if word[: -len(suf)] in _FA_STOP:
                return True
    return False

# Tokens that are pure punctuation / digits / url junk
_JUNK_RE = re.compile(r"(^https?$|^www|^<|>$|=|\"|http|\\d+$)")

_TRIM_CHARS = ".,:;!?()[]{}\"'«»…—–؟،؛ٌٍَُِّْٔ"

_MIN_WORD_LEN = 2  # Persian words can be short (۲ chars like «AI» kept too)


def extract_keywords(question: str) -> list[str]:
    """Extract meaningful keywords from a Persian/English question.

    - Lowercases, strips punctuation from word edges.
    - Drops English + Persian stopwords, HTML/url junk, digits.
    - Keeps order of first appearance, deduplicated.
    """
    if not question or not question.strip():
        return []
    # normalize arabic ي/ك to persian ی/ک — very common mixing
    q = question.replace("ي", "ی").replace("ك", "ک")
    words = [w.strip(_TRIM_CHARS).lower() for w in q.split()]
    out: list[str] = []
    seen: set[str] = set()
    for w in words:
        if not w or len(w) < _MIN_WORD_LEN:
            continue
        if w in _EN_STOP or _is_fa_stop(w):
            continue
        if w.isdigit() or _JUNK_RE.search(w):
            continue
        if w not in seen:
            seen.add(w)
            out.append(w)
    # Persian transliterations → also add the English alias so Persian
    # questions can hit English archive titles / web pages. Lookup accepts
    # suffixed forms (تراشه‌ها، دیپ‌سیک‌ها ...) via _alias_for.
    for w in list(out):
        alias = _alias_for(w)
        if alias and alias not in seen:
            seen.add(alias)
            out.append(alias)
    return out[:16]  # cap: keep the question focused


def _alias_for(word: str) -> str | None:
    """Look up a Persian word in _FA_ALIAS, tolerating suffixes/ZWNJ joins."""
    if word in _FA_ALIAS:
        return _FA_ALIAS[word]
    # split off ZWNJ-joined suffixes: تراشه‌های → تراشه + های
    parts = word.split("\u200c")  # ZWNJ
    if len(parts) > 1 and parts[-1] in _FA_SUFFIXES:
        base = "\u200c".join(parts[:-1])
        if base in _FA_ALIAS:
            return _FA_ALIAS[base]
    for suf in _FA_SUFFIXES:
        if word.endswith(suf) and len(word) > len(suf) + 1:
            base = word[: -len(suf)]
            if base in _FA_ALIAS:
                return _FA_ALIAS[base]
            base2 = base + "\u200c" + suf
            if base2 in _FA_ALIAS:  # pragma: no cover - defensive
                return _FA_ALIAS[base2]
    return None


# ---------------------------------------------------------------------------
# Archive search (items table)
# ---------------------------------------------------------------------------

def _archive_search(db: Session, keywords: list[str], limit: int) -> list[dict]:
    """Search internal items (ai_relevant=True) by keywords.

    Matches title/summary ILIKE plus category/camp/actor equality. Score =
    weighted keyword hits (title counts double) + item score + recency.
    Returns [{title, url, snippet, kind, published_at, score}].
    """
    if not keywords or db is None:
        return []

    try:
        cols = "id, title, url, summary, category, camp, actor, published_at, score"
        like_title = " OR ".join(f"title ILIKE :kw{i}" for i in range(len(keywords)))
        like_summ = " OR ".join(f"summary ILIKE :kw{i}" for i in range(len(keywords)))
        where = (
            f"ai_relevant = true AND ({like_title} OR {like_summ})"
        )
        params = {f"kw{i}": f"%{w}%" for i, w in enumerate(keywords)}
        # keep query fast even on large archives: fetch a candidate pool
        rows = db.execute(
            sql_text(f"SELECT {cols} FROM items WHERE {where}"),
            params,
        ).fetchall()
    except Exception as e:
        log.warning("archive keyword search failed: %s", e)
        return []

    now = datetime.now(timezone.utc)
    results: list[dict] = []
    for r in rows:
        (iid, title, url, summary, category, camp, actor, published_at, score) = r
        low_title = (title or "").lower()
        low_summ = (summary or "").lower()
        kw_hits = 0
        for kw in keywords:
            if kw in low_title:
                kw_hits += 2
            elif kw in low_summ:
                kw_hits += 1
        relevance = min(kw_hits / max(2 * len(keywords), 2), 1.0)
        # item's own score (0..1-ish)
        item_score = float(score or 0.0)
        # recency: newer is better, decays over 90 days
        recency = 0.0
        if published_at:
            try:
                pd = published_at if published_at.tzinfo else published_at.replace(tzinfo=timezone.utc)
                age_days = max((now - pd).total_seconds() / 86400.0, 0.0)
                recency = max(0.0, 1.0 - age_days / 90.0)
            except Exception:
                recency = 0.0
        total = 0.55 * relevance + 0.25 * item_score + 0.20 * recency
        results.append(
            {
                "title": title or "",
                "url": url or "",
                "snippet": (summary or "")[:300],
                "kind": "archive",
                "published_at": published_at.isoformat() if published_at else None,
                "_score": total,
            }
        )
    results.sort(key=lambda x: x["_score"], reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# Web search with a hard time budget
# ---------------------------------------------------------------------------

_SEARX_UA = "AI-Sentinel/0.1 (chatbot research agent)"

_ARTICLE_RE = re.compile(r"<article[^>]*result[^>]*>.*?</article>", re.DOTALL)
_H3_LINK_RE = re.compile(r'<h3><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h3>', re.DOTALL)
_CONTENT_P_RE = re.compile(r'<p[^>]*class="content[^"]*"[^>]*>(.*?)</p>', re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_ENTITY_MAP = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'"}
_WS_RE = re.compile(r"\s+")


def _searxng_html_fallback(query: str, limit: int) -> list[dict]:
    """Fallback for SearXNG instances where the JSON format is disabled (403).

    Fetches the HTML results page and parses ``<article class="result">``
    entries: title from the h3 anchor, url from its href, snippet from the
    ``p.content`` paragraph. Returns [{title, url, snippet}].
    """
    try:
        from app.config import settings

        base = settings.searxng_url
    except Exception:
        base = "http://localhost:8080"
    try:
        import httpx

        resp = httpx.get(
            f"{base}/search",
            params={"q": query},
            timeout=WEB_TIMEOUT_SECONDS,
            headers={"User-Agent": _SEARX_UA, "Accept": "text/html"},
            follow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as e:
        log.warning("searxng html fallback failed: %s", e)
        return []

    out: list[dict] = []
    seen_urls: set[str] = set()
    for art in _ARTICLE_RE.findall(resp.text):
        if len(out) >= limit:
            break
        m = _H3_LINK_RE.search(art)
        if not m:
            continue
        url, raw_title = m.group(1), m.group(2)
        if not url.startswith(("http://", "https://")) or url in seen_urls:
            continue
        seen_urls.add(url)
        title = _WS_RE.sub(" ", _TAG_RE.sub("", raw_title)).strip()
        snippet = ""
        pm = _CONTENT_P_RE.search(art)
        if pm:
            snippet = _WS_RE.sub(" ", _TAG_RE.sub("", pm.group(1))).strip()
        for ent, rep in _ENTITY_MAP.items():
            title = title.replace(ent, rep)
            snippet = snippet.replace(ent, rep)
        if title:
            out.append({"title": title[:200], "url": url, "snippet": snippet[:300]})
    return out


# Shared executor so a hung web call can be abandoned on timeout instead of
# blocking the request thread on executor shutdown (web_search.py's own httpx
# timeout eventually reaps the abandoned worker).
_WEB_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="chat-web")


def _web_search_budgeted(keywords: list[str], limit: int) -> list[dict]:
    """Run web_search with a hard 10s budget.

    Tries the shared ``web_search`` adapter first (JSON). If the provider is
    SearXNG and JSON is unavailable (some instances disable the format → 403),
    falls back to parsing the HTML results page. Returns
    [{title, url, snippet, kind, published_at, _score}].
    """
    if not keywords:
        return []
    # Build two queries: one with all keywords (mixed FA+EN), 
    # and one with only English aliases for better web results
    en_keywords = [w for w in keywords if w.isascii()]
    fa_keywords = [w for w in keywords if not w.isascii()]
    # Primary query: English keywords first (better for web), then Persian
    if en_keywords:
        query = " ".join(en_keywords)
    else:
        query = " ".join(keywords)
    started = time.monotonic()
    raw: list[dict] = []
    try:
        future = _WEB_POOL.submit(web_search, query, limit)
        raw = future.result(timeout=WEB_TIMEOUT_SECONDS) or []
    except TimeoutError:
        future.cancel()
        log.warning(
            "web search exceeded %.0fs budget — archive-only answer", WEB_TIMEOUT_SECONDS
        )
        return []
    except Exception as e:
        log.warning("web search failed: %s", e)
        raw = []

    if not raw:
        # JSON path empty (format disabled / provider hiccup) → HTML fallback
        try:
            from app.config import settings

            provider_is_searx = settings.web_search_provider == "searxng"
        except Exception:
            provider_is_searx = False
        if provider_is_searx:
            try:
                raw = _searxng_html_fallback(query, limit)
            except Exception as e:
                log.warning("searxng html fallback raised: %s", e)
                raw = []
    if not raw:
        return []
    elapsed = time.monotonic() - started
    out: list[dict] = []
    n = max(len(raw), 1)
    for i, r in enumerate(raw or []):
        # position-based score: first result ≈ 0.9, decaying to ≈0.4
        pos_score = 0.9 - 0.5 * (i / n)
        out.append(
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "kind": "web",
                "published_at": None,
                "_score": pos_score,
            }
        )
    log.info("web search returned %d results in %.1fs", len(out), elapsed)
    return out


# ---------------------------------------------------------------------------
# Merge + rank
# ---------------------------------------------------------------------------

def _merge_rank(archive: list[dict], web: list[dict], limit: int) -> list[dict]:
    """Merge archive + web sources and rank by relevance score.

    Archive hits get a small internal-trust bonus (the user curated those).
    Returns top `limit` items with ref_no assigned 1..n.
    """
    merged = []
    for s in archive:
        s = dict(s)
        s["_score"] = s.get("_score", 0.0) + 0.08  # archive trust bonus
        merged.append(s)
    merged.extend(dict(s) for s in web)
    merged.sort(key=lambda x: x.get("_score", 0.0), reverse=True)
    top = merged[:limit]
    for i, s in enumerate(top, start=1):
        s["ref_no"] = i
    return top


# ---------------------------------------------------------------------------
# Answer composition (no LLM needed)
# ---------------------------------------------------------------------------

_FA_ARC_LABEL = "آرشیو داخلی"
_FA_WEB_LABEL = "وب"


def _clean_text(t: str | None, max_len: int = 180) -> str:
    if not t:
        return ""
    t = " ".join(t.split())
    return t[:max_len]


def _compose_answer(question: str, sources: list[dict]) -> str:
    """Build the structured Persian answer from ranked sources (no LLM)."""
    n_arc = sum(1 for s in sources if s.get("kind") == "archive")
    n_web = sum(1 for s in sources if s.get("kind") == "web")
    total = len(sources)

    if total == 0:
        return (
            "چیزی در آرشیو/وب پیدا نشد — سؤال را دقیق‌تر بپرسید"
            " (مثلاً نام شرکت، نام مدل، یا موضوع دقیق‌تری مثل «مدل‌های DeepSeek» یا « Nvidia GPU export»."
        )

    lines: list[str] = []
    lines.append(f"بر اساس {total} منبع ({n_arc} از {_FA_ARC_LABEL}، {n_web} از {_FA_WEB_LABEL}):")
    lines.append("")

    # 3-5 bullets: most important findings from titles/snippets
    bullets = sources[:5]
    for s in bullets:
        title = _clean_text(s.get("title"), 140) or "(بدون عنوان)"
        snip = _clean_text(s.get("snippet"), 160)
        ref = s.get("ref_no")
        bullet = f"• {title}"
        if snip:
            bullet += f" — {snip}"
        if ref:
            bullet += f" [{ref}]"
        lines.append(bullet)
    if bullets:
        lines.append("")

    # numbered sources
    lines.append("منابع مرتبط:")
    for s in sources:
        ref = s.get("ref_no", "?")
        title = _clean_text(s.get("title"), 120) or "(بدون عنوان)"
        snip = _clean_text(s.get("snippet"), 200)
        kind = s.get("kind", "web")
        kind_fa = _FA_ARC_LABEL if kind == "archive" else _FA_WEB_LABEL
        line = f"[{ref}] {title} ({kind_fa})"
        if snip:
            line += f" — {snip}"
        lines.append(line)

    return "\n".join(lines)


def _compose_answer_two_sections(question: str, recent: list[dict], historical: list[dict]) -> str:
    """Build answer with two sections: recent news + important historical."""
    total = len(recent) + len(historical)
    n_web = sum(1 for s in recent + historical if s.get("kind") == "web")
    n_arc = total - n_web

    if total == 0:
        return (
            "چیزی در آرشیو/وب پیدا نشد — سؤال را دقیق‌تر بپرسید"
            " (مثلاً نام شرکت، نام مدل، یا موضوع دقیق‌تر)."
        )

    lines: list[str] = []
    lines.append(f"بر اساس {total} منبع ({n_arc} از {_FA_ARC_LABEL}، {n_web} از {_FA_WEB_LABEL}):")
    lines.append("")

    if recent:
        lines.append("## 📰 جدیدترین اخبار و نتایج")
        lines.append("")
        for s in recent[:6]:
            title = _clean_text(s.get("title"), 140) or "(بدون عنوان)"
            snip = _clean_text(s.get("snippet"), 160)
            ref = s.get("ref_no")
            kind = "🌐" if s.get("kind") == "web" else "📁"
            bullet = f"• {kind} {title}"
            if snip:
                bullet += f" — {snip}"
            if ref:
                bullet += f" [{ref}]"
            lines.append(bullet)
        lines.append("")

    if historical:
        lines.append("## 📚 مهم‌ترین منابع آرشیو")
        lines.append("")
        for s in historical[:6]:
            title = _clean_text(s.get("title"), 140) or "(بدون عنوان)"
            snip = _clean_text(s.get("snippet"), 160)
            ref = s.get("ref_no")
            bullet = f"• 📁 {title}"
            if snip:
                bullet += f" — {snip}"
            if ref:
                bullet += f" [{ref}]"
            lines.append(bullet)
        lines.append("")

    # Numbered sources list
    lines.append("منابع مرتبط:")
    for s in recent + historical:
        ref = s.get("ref_no", "?")
        title = _clean_text(s.get("title"), 120) or "(بدون عنوان)"
        kind = s.get("kind", "web")
        kind_fa = _FA_ARC_LABEL if kind == "archive" else _FA_WEB_LABEL
        lines.append(f"[{ref}] {title} ({kind_fa})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM (optional enhancement)
# ---------------------------------------------------------------------------

CHAT_SYSTEM = """You are a Persian-speaking AI research assistant inside a chat.
Answer the user's question using ONLY the provided sources. Cite them inline
with numbered references like [1], [2]. Answer in Persian unless the question
is in English. Be factual and concise."""


def _llm_enhance(question: str, sources: list[dict]) -> str:
    """If an LLM key is configured, get an LLM answer; empty string otherwise."""
    if not sources:
        return ""
    try:
        context = "\n\n".join(
            f"[{s.get('ref_no')}] {s.get('title', '')}\nURL: {s.get('url', '')}\n{s.get('snippet', '')}"
            for s in sources
        )
        prompt = f"Question: {question}\n\nSources:\n{context}\n\nAnswer (with [n] citations):"
        return llm_complete(prompt, system=CHAT_SYSTEM) or ""
    except Exception as e:
        log.warning("LLM enhancement failed: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def _safe_archive(db: Session, keywords: list[str], limit: int) -> list[dict]:
    """_archive_search that never raises (for use inside a worker thread)."""
    try:
        return _archive_search(db, keywords, limit)
    except Exception as e:
        log.warning("archive search raised: %s", e)
        return []


def chat_retrieve(question: str, online: bool = True, limit: int = 8, db: Session | None = None) -> dict:
    """Answer a chat question by searching internal archive + live web.

    Returns ``{"answer": str, "sources": [...], "online": bool,
    "recent_sources": [...], "archive_sources": [...]}`` where:
    - recent_sources = latest news/web results for the query
    - archive_sources = most important historical items from internal DB
    Each source is ``{ref_no, title, url, snippet, kind, published_at}``.
    Never raises: DB/web failures degrade to archive-only or empty results.
    """
    keywords = extract_keywords(question)

    own_session = False
    if db is None:
        db = _get_session()
        own_session = db is not None
    try:
        archive: list[dict] = []
        web: list[dict] = []
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="chat") as pool:
            archive_fut = pool.submit(_safe_archive, db, keywords, limit * 2)
            web_fut = (
                pool.submit(_web_search_budgeted, keywords, limit * 2)
                if (online and keywords)
                else None
            )
            archive = archive_fut.result()
            if web_fut is not None:
                web = web_fut.result()
    finally:
        if own_session and db is not None:
            db.close()

    online_used = bool(online)
    if online and not web:
        online_used = False

    # Split into two sections:
    # 1. recent_sources = newest items (web + recent archive)
    # 2. archive_sources = most important historical items
    all_sources = _merge_rank(archive, web, limit * 2)

    # Recent: web results + archive items from last 30 days, sorted by recency
    recent_sources = []
    archive_sources = []
    now_ts = datetime.now(timezone.utc)
    for s in all_sources:
        if s.get("kind") == "web":
            recent_sources.append(s)
        elif s.get("published_at"):
            try:
                pub = datetime.fromisoformat(s["published_at"])
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                age_days = (now_ts - pub).total_seconds() / 86400.0
                if age_days <= 30:
                    recent_sources.append(s)
                else:
                    archive_sources.append(s)
            except Exception:
                archive_sources.append(s)
        else:
            archive_sources.append(s)

    # Cap each section
    recent_sources = recent_sources[:limit]
    archive_sources = archive_sources[:limit]

    # Renumber refs across both sections
    all_final = recent_sources + archive_sources
    for i, s in enumerate(all_final, start=1):
        s["ref_no"] = i

    # Compose answer with two sections
    answer = _compose_answer_two_sections(question, recent_sources, archive_sources)

    # Optional LLM layer
    llm_answer = _llm_enhance(question, all_final)
    if llm_answer:
        answer = f"{llm_answer}\n\n—\n{answer}"

    # Clean output
    def _clean_source(s: dict) -> dict:
        return {
            "ref_no": s.get("ref_no"),
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "snippet": s.get("snippet", ""),
            "kind": s.get("kind", "web"),
            "published_at": s.get("published_at"),
        }

    return {
        "answer": answer,
        "sources": [_clean_source(s) for s in all_final],
        "recent_sources": [_clean_source(s) for s in recent_sources],
        "archive_sources": [_clean_source(s) for s in archive_sources],
        "online": online_used,
    }


# Convenience: session factory for standalone use (tests, CLI).
def _get_session() -> Session | None:
    try:
        from app.db import SessionLocal

        return SessionLocal()
    except Exception as e:
        log.warning("could not create DB session: %s", e)
        return None


def chat_retrieve_auto(question: str, online: bool = True, limit: int = 8) -> dict:
    """chat_retrieve with automatic session management (for CLI/tests)."""
    session = _get_session()
    try:
        return chat_retrieve(question, online=online, limit=limit, db=session)
    finally:
        if session is not None:
            session.close()
