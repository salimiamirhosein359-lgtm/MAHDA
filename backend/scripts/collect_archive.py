"""AI Sentinel — archive collector: 2 years of AI data (Oct 2024 → Oct 2026).

Gathers historical items from free, no-key APIs and stores them in PostgreSQL:

  1. arXiv API            — papers (cs.AI, cs.CL, cs.LG, cs.CV, cs.NE, stat.ML)
                            submitted in the window, 300/request, 3s sleep.
  2. Hacker News Algolia  — full story archive mentioning AI in the window,
                            month-by-month slices with quality points filter.
  3. Open Library         — AI books published 2024-2026 (sort=new).
  4. Semantic Scholar     — academic papers 2024-2026 (best-effort; currently
                            hard rate-limited without an API key).
  5. RSS feeds            — re-pull the seed_sources feeds, keeping entries
                            published inside the window.

Classification uses app.pipeline.rules.classify_by_rules() (NO LLM), following
the backfill_rules.py pattern. Dedup on (source_id, external_id). All
published_at values are stored as naive UTC. Safe to re-run: already-stored
items are skipped (idempotent).

Run from the backend folder:
    python scripts/collect_archive.py
(with proxy if needed:  $env:HTTPS_PROXY="http://127.0.0.1:10808")
"""
import sys
import time
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# make `app` importable when run as `python scripts/collect_archive.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Item, Source  # noqa: E402
from app.pipeline.rules import classify_by_rules, strip_html  # noqa: E402

log = logging.getLogger("ai_sentinel.collect_archive")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

UA = {"User-Agent": "ai-sentinel/0.1 (archive-collector; research use)"}

# ---------------------------------------------------------------------------
# Window: Oct 27 2024 → Oct 28 2026 (naive UTC)
# ---------------------------------------------------------------------------
WINDOW_START = datetime(2024, 10, 27)
WINDOW_END = datetime(2026, 10, 28)
ARXIV_START = "202410270000"
ARXIV_END = "202610280000"

ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.NE", "stat.ML"]
ARXIV_API = "http://export.arxiv.org/api/query"
HN_API = "https://hn.algolia.com/api/v1/search_by_date"
OL_API = "https://openlibrary.org/search.json"
S2_API = "https://api.semanticscholar.org/graph/v1/paper/search"

# ---------------------------------------------------------------------------
# HTTP helper with retries
# ---------------------------------------------------------------------------

def http_get(url: str, params: dict | None = None, timeout: float = 60.0,
             retries: int = 3, backoff: float = 5.0) -> httpx.Response | None:
    """GET with retry/backoff; returns None on final failure."""
    for attempt in range(retries):
        try:
            r = httpx.get(url, params=params, headers=UA, timeout=timeout,
                          follow_redirects=True)
            if r.status_code == 429:
                wait = backoff * (attempt + 2)
                log.warning("429 from %s — sleeping %.0fs", url.split("?")[0], wait)
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                time.sleep(backoff)
                continue
            r.raise_for_status()
            return r
        except Exception as e:
            log.warning("GET %s failed (attempt %d): %s", url.split("?")[0], attempt + 1, e)
            time.sleep(backoff)
    return None


def to_naive_utc(dt: datetime) -> datetime:
    """Strip timezone, converting to UTC first (Postgres column is naive UTC)."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_dt(s: str) -> datetime | None:
    if not s:
        return None
    try:
        from dateutil import parser as dparser
        return to_naive_utc(dparser.parse(s))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Source helpers
# ---------------------------------------------------------------------------

def get_or_create_source(db, name: str, kind: str, group: str, camp: str,
                         weight: float, config: dict) -> Source:
    src = db.execute(select(Source).where(Source.name == name)).scalar()
    if src is None:
        src = Source(name=name, kind=kind, group=group, camp=camp,
                     weight=weight, config=config or {})
        db.add(src)
        db.commit()
        log.info("created source %s", name)
    return src


# ---------------------------------------------------------------------------
# 1. arXiv
# ---------------------------------------------------------------------------

def _arxiv_fetch_page(query: str, start: int, max_results: int,
                      seen: set[str], items: list[dict]) -> int:
    """Fetch one arXiv API page, parse entries into items. Returns entries fetched."""
    import re
    import lxml.etree as etree
    ns = {"a": "http://www.w3.org/2005/Atom"}

    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": str(start),
        "max_results": str(max_results),
    }
    r = http_get(ARXIV_API, params=params, timeout=60)
    if r is None:
        log.error("arxiv request failed at start=%d", start)
        return 0
    try:
        root = etree.fromstring(r.content)
    except Exception as e:
        log.error("arxiv XML parse failed: %s", e)
        return 0

    entries = root.findall("a:entry", ns)
    for entry in entries:
        published_raw = entry.findtext("a:published", default="", namespaces=ns)
        published = None
        if published_raw:
            published = datetime.fromisoformat(
                published_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        if published is None or not (WINDOW_START <= published <= WINDOW_END):
            continue

        arxiv_url = entry.findtext("a:id", default="", namespaces=ns) or ""
        m = re.search(r"abs/(.+?)(v\d+)?$", arxiv_url)
        external_id = f"arxiv:{m.group(1)}" if m else f"arxiv-url:{hash(arxiv_url)}"

        if external_id in seen:
            continue
        seen.add(external_id)

        cats = [c.get("term") for c in entry.findall("a:category", ns)]
        authors = [a.findtext("a:name", default="", namespaces=ns)
                   for a in entry.findall("a:author", ns)]

        items.append({
            "external_id": external_id,
            "title": " ".join(entry.findtext("a:title", default="", namespaces=ns).split())[:1000],
            "url": arxiv_url,
            "summary": " ".join(entry.findtext("a:summary", default="", namespaces=ns).split())[:2000],
            "author": ", ".join(authors[:5]) or None,
            "published_at": published,
            "item_type": "paper",
            "meta": {"primary_category": (cats[0] if cats else None),
                     "categories": cats},
        })
    return len(entries)


def collect_arxiv(per_request: int = 300, target: int = 2400,
                  pause: float = 3.0, pages_per_month: int = 1) -> list[dict]:
    """Page through the newest cs.AI/CL/LG/CV/NE + stat.ML papers in the window.

    A single descending query only reaches back ~10 days at 300/page, so the
    window is sliced month by month (up to pages_per_month × 300 newest
    papers per month) to cover the full 2-year span.
    """
    cat_q = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    items: list[dict] = []
    seen: set[str] = set()

    # month slices from newest to oldest
    months: list[tuple[datetime, datetime]] = []
    cur = WINDOW_END
    while cur > WINDOW_START:
        first = cur.replace(day=1)
        lo = max(first, WINDOW_START)
        hi = min(cur, WINDOW_END)
        if lo < hi:
            months.append((lo, hi))
        if first <= WINDOW_START:
            break
        cur = first - timedelta(days=1)

    for lo, hi in months:
        q = (f"({cat_q}) AND submittedDate:[{lo.strftime('%Y%m%d%H%M')} "
             f"TO {hi.strftime('%Y%m%d%H%M')}]")
        before = len(items)
        start = 0
        # up to `pages_per_month` pages of 300 per month slice (newest first)
        for _ in range(pages_per_month):
            n = _arxiv_fetch_page(q, start, per_request, seen, items)
            if n == 0:
                break
            start += n
            if n < per_request:
                break
            time.sleep(pause)
        log.info("arxiv %s..%s: +%d items (total %d)",
                 lo.date(), hi.date(), len(items) - before, len(items))
        if len(items) >= target:
            break
        time.sleep(pause)

    log.info("arxiv total window items: %d", len(items))
    return items


# ---------------------------------------------------------------------------
# 2. Hacker News (Algolia archive) — time-sliced with recursive bisection
# ---------------------------------------------------------------------------

HN_PAGE_CAP = 1000  # Algolia max hitsPerPage / max browsable hits per query


def collect_hackernews(points_min: int = 50, pause: float = 1.0,
                       max_items: int = 8000) -> list[dict]:
    """Walk the 2-year window month by month; fetch AI stories above a
    minimum points threshold.

    Algolia caps browsable results at 1000 hits per query, so a month is
    probed first (hitsPerPage=1); if it has more than ~900 hits it is split
    recursively into half-month / week / day slices until every slice fits
    under the cap. Keeps pagination depth = 1 (nbPages == 1) for all slices.
    """
    items: list[dict] = []
    seen: set[str] = set()

    def probe_count(t0: int, t1: int) -> int:
        numeric = f"created_at_i>{t0},created_at_i<{t1},points>{points_min}"
        r = http_get(HN_API, params={"query": "AI", "tags": "story",
                                     "numericFilters": numeric,
                                     "hitsPerPage": 1}, timeout=60,
                     retries=2)
        if r is None:
            return -1
        return r.json().get("nbHits", 0)

    def fetch_slice(t0: int, t1: int) -> list[dict]:
        numeric = f"created_at_i>{t0},created_at_i<{t1},points>{points_min}"
        r = http_get(HN_API, params={"query": "AI", "tags": "story",
                                     "numericFilters": numeric,
                                     "hitsPerPage": HN_PAGE_CAP, "page": 0},
                     timeout=90, retries=2)
        if r is None:
            log.error("HN slice fetch failed: %s", numeric)
            return []
        d = r.json()
        hits = d.get("hits", [])
        # if the API still reports more pages, log a warning (should not happen)
        if (d.get("nbPages") or 1) > 1:
            log.warning("HN slice overflows cap (%s pages) — may be truncated", d.get("nbPages"))
        return hits

    def collect_range(t0: int, t1: int, depth: int = 0) -> list[dict]:
        """Recursively split [t0, t1) until each slice fits under the cap."""
        nb = probe_count(t0, t1)
        if nb < 0:
            return []
        if nb <= HN_PAGE_CAP - 100:
            return fetch_slice(t0, t1)
        span = t1 - t0
        if span <= 86400:  # one day and still too many — give up gracefully
            log.warning("HN day slice still %d hits — fetching first page only", nb)
            return fetch_slice(t0, t1)
        mid = t0 + span // 2
        left = collect_range(t0, mid, depth + 1)
        time.sleep(pause)
        right = collect_range(mid, t1, depth + 1)
        return left + right

    start = WINDOW_START
    while start < WINDOW_END and len(items) < max_items:
        if start.month == 12:
            next_month = datetime(start.year + 1, 1, 1)
        else:
            next_month = datetime(start.year, start.month + 1, 1)
        month_end = min(next_month, WINDOW_END + timedelta(days=1))
        t0 = int(start.replace(tzinfo=timezone.utc).timestamp())
        t1 = int(month_end.replace(tzinfo=timezone.utc).timestamp())

        hits = collect_range(t0, t1)

        month_new = 0
        for h in hits:
            oid = str(h.get("objectID") or "")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            published = parse_dt(h.get("created_at") or "")
            if published is None or not (WINDOW_START <= published <= WINDOW_END):
                continue
            title = strip_html(str(h.get("title") or ""))[:1000]
            if not title:
                continue
            url_ = h.get("url") or f"https://news.ycombinator.com/item?id={oid}"
            story_text = strip_html(str(h.get("story_text") or ""))[:2000] or None
            items.append({
                "external_id": f"hn:{oid}",
                "title": title,
                "url": url_,
                "summary": story_text or (f"HN discussion: {h.get('points')} points, "
                                          f"{h.get('num_comments')} comments."),
                "author": h.get("author"),
                "published_at": published,
                "item_type": "news",
                "meta": {"points": h.get("points"),
                         "num_comments": h.get("num_comments"),
                         "query": "AI"},
            })
            month_new += 1

        log.info("HN %d-%02d: %d hits → %d new (total %d)",
                 start.year, start.month, len(hits), month_new, len(items))
        start = next_month
        time.sleep(pause)

    log.info("HN total window items: %d (points>=%d)", len(items), points_min)
    return items


# ---------------------------------------------------------------------------
# 3. Open Library
# ---------------------------------------------------------------------------

def collect_openlibrary(queries: list[str], per_query: int = 200,
                        pause: float = 2.0) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for q in queries:
        r = http_get(OL_API, params={"q": q, "sort": "new", "limit": per_query,
                                     "fields": "title,author_name,first_publish_year,publish_year,key,isbn"},
                     timeout=90)
        if r is None:
            log.error("openlibrary request failed for q=%r", q)
            continue
        docs = r.json().get("docs", [])
        for doc in docs:
            years = doc.get("publish_year") or []
            fpy = doc.get("first_publish_year")
            year = fpy if fpy in (2024, 2025, 2026) else (max([y for y in years if y in (2024, 2025, 2026)], default=None))
            if year is None:
                continue  # only books published in our window
            key = doc.get("key") or ""
            if not key or key in seen:
                continue
            seen.add(key)
            title = strip_html(str(doc.get("title") or ""))[:1000]
            if not title:
                continue
            authors = doc.get("author_name") or []
            isbns = doc.get("isbn") or []
            items.append({
                "external_id": f"ol:{key}",
                "title": title,
                "url": f"https://openlibrary.org{key}",
                "summary": f"Book published {year}." + (f" ISBN: {isbns[0]}." if isbns else ""),
                "author": ", ".join(authors[:5]) or None,
                "published_at": datetime(year, 1, 1),
                "item_type": "book",
                "meta": {"query": q, "publish_year": year,
                         "isbn": isbns[:3]},
            })
        log.info("openlibrary q=%r: %d docs → %d books so far", q, len(docs), len(items))
        time.sleep(pause)
    log.info("openlibrary total: %d", len(items))
    return items


# ---------------------------------------------------------------------------
# 4. Semantic Scholar (best-effort — shared pool is heavily 429-limited)
# ---------------------------------------------------------------------------

def collect_semanticscholar(queries: list[str], per_query: int = 100,
                            pause: float = 3.0, max_429: int = 3) -> list[dict]:
    """Best-effort: the keyless S2 pool is heavily rate-limited (shared).

    Retries with exponential backoff; gives up after max_429 consecutive
    failed queries and returns what it has so far.
    """
    items: list[dict] = []
    seen: set[str] = set()
    consecutive_fail = 0

    def s2_get(params: dict) -> httpx.Response | None:
        backoff = 30.0
        for attempt in range(4):
            r = http_get(S2_API, params=params, timeout=60, retries=1)
            if r is not None and r.status_code == 200:
                return r
            log.warning("S2 attempt %d failed — backing off %.0fs", attempt + 1, backoff)
            time.sleep(backoff)
            backoff *= 2
        return None

    for q in queries:
        r = s2_get({"query": q, "year": "2024-2026", "limit": per_query,
                    "fields": "title,abstract,year,authors,url,venue"})
        if r is None:
            consecutive_fail += 1
            log.warning("semanticscholar failed for q=%r (streak %d)", q, consecutive_fail)
            if consecutive_fail >= max_429:
                log.error("semanticscholar: giving up after %d consecutive failures",
                          consecutive_fail)
                break
            continue
        consecutive_fail = 0
        data = r.json().get("data", [])
        for p in data:
            pid = p.get("paperId") or p.get("url") or ""
            if not pid or pid in seen:
                continue
            seen.add(pid)
            year = p.get("year")
            published = datetime(year, 1, 1) if year in (2024, 2025, 2026) else None
            authors = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:5])
            items.append({
                "external_id": f"s2:{pid}",
                "title": strip_html(str(p.get("title") or ""))[:1000],
                "url": p.get("url") or "",
                "summary": strip_html(str(p.get("abstract") or ""))[:2000] or None,
                "author": authors or None,
                "published_at": published,
                "item_type": "paper",
                "meta": {"venue": p.get("venue"), "year": year, "query": q},
            })
        log.info("semanticscholar q=%r: %d papers (total %d)", q, len(data), len(items))
        time.sleep(pause)
    log.info("semanticscholar total: %d", len(items))
    return items


# ---------------------------------------------------------------------------
# 5. RSS (seed feeds)
# ---------------------------------------------------------------------------

def collect_rss_feeds() -> dict[str, list[dict]]:
    """Pull each seed RSS feed; keep entries inside the archive window."""
    from app.collectors.seed_sources import SEED_SOURCES
    import feedparser

    out: dict[str, list[dict]] = {}
    for seed in SEED_SOURCES:
        if seed["kind"] != "rss":
            continue
        feed_url = seed["config"].get("url")
        if not feed_url:
            continue
        try:
            parsed = feedparser.parse(feed_url)
            entries = parsed.entries or []
        except Exception as e:
            log.warning("rss %s failed: %s", seed["name"], e)
            out[seed["name"]] = []
            continue
        items: list[dict] = []
        for entry in entries:
            guid = getattr(entry, "id", None) or getattr(entry, "link", "") or getattr(entry, "title", "")
            published = None
            for key in ("published", "updated"):
                raw = getattr(entry, key, None)
                if raw:
                    published = parse_dt(str(raw))
                    break
            # keep only entries published inside the window (or undated)
            if published is not None and not (
                WINDOW_START - timedelta(days=2) <= published <= WINDOW_END + timedelta(days=2)
            ):
                continue
            items.append({
                "external_id": f"rss:{guid}",
                "title": strip_html(getattr(entry, "title", "") or "")[:1000],
                "url": getattr(entry, "link", "") or "",
                "summary": strip_html(getattr(entry, "summary", "") or "")[:2000] or None,
                "author": getattr(entry, "author", None),
                "published_at": published,
                "item_type": "news",
                "meta": {"feed": feed_url, "source_name": seed["name"]},
            })
        out[seed["name"]] = items
        log.info("rss %s: %d entries in window", seed["name"], len(items))
    return out


# ---------------------------------------------------------------------------
# Ingest (rules-based classification, dedup, naive-UTC published_at)
# ---------------------------------------------------------------------------

def ingest_archive_items(db, source: Source, raw_items: list[dict]) -> tuple[int, int]:
    """Insert new items with rules classification. Returns (new, skipped_dup)."""
    new_count = 0
    dup_count = 0

    # preload existing external ids for this source in one query
    existing = set(
        db.execute(
            select(Item.external_id).where(Item.source_id == source.id)
        ).scalars()
    )

    for raw in raw_items:
        external_id = str(raw["external_id"])
        if external_id in existing:
            dup_count += 1
            continue
        if not raw.get("title") or not raw.get("url"):
            dup_count += 1
            continue
        existing.add(external_id)

        published = raw.get("published_at")
        if published is not None:
            published = to_naive_utc(published)

        summary = strip_html(raw.get("summary") or "")[:2000] or None

        text_for_rules = f"{raw['title']} {summary or ''}"
        res = classify_by_rules(text_for_rules)

        category = res["category"] if res["category"] != "other" else (
            "models" if source.group == "A" and source.kind in ("arxiv", "semanticscholar") else res["category"]
        )
        camp = res["camp"]
        if source.camp in ("US", "CN", "EU"):
            camp = source.camp
        actor = res["actor"]

        item = Item(
            source_id=source.id,
            external_id=external_id,
            title=str(raw["title"])[:1000],
            url=str(raw["url"]),
            summary=summary,
            author=(raw.get("author") or None) and str(raw["author"])[:300],
            published_at=published,
            item_type=raw.get("item_type", "news"),
            ai_relevant=True,
            category=category,
            camp=camp,
            actor=actor,
            meta=raw.get("meta") or {},
        )
        db.add(item)
        new_count += 1
        if new_count % 500 == 0:
            db.commit()
            log.info("  … committed %d new items for %s", new_count, source.name)

    db.commit()
    source.last_fetched_at = datetime.utcnow()
    db.commit()
    return new_count, dup_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # optional source selector:  python scripts/collect_archive.py arxiv
    only = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    log.info("=" * 60)
    log.info("AI Sentinel archive collection: %s -> %s (only=%s)",
             WINDOW_START, WINDOW_END, only)
    log.info("=" * 60)

    db = SessionLocal()
    stats: dict[str, int] = {}
    errors: list[str] = []

    try:
        before = db.execute(text("SELECT count(*) FROM items")).scalar()
        log.info("items before: %d", before)

        # --- 1. arXiv ---------------------------------------------------
        if only in ("all", "arxiv"):
            try:
                src = get_or_create_source(db, "arxiv", "arxiv", "A", "other", 0.9,
                                           {"window": "2024-10-27/2026-10-28"})
                raw = collect_arxiv(target=7200, pages_per_month=1)
                stats["arxiv"] = ingest_archive_items(db, src, raw)[0]
            except Exception as e:
                log.exception("arxiv failed")
                errors.append(f"arxiv: {e}")
                db.rollback()

        # --- 2. Hacker News ---------------------------------------------
        if only in ("all", "hn", "hackernews"):
            try:
                src = get_or_create_source(db, "hackernews-ai", "hn", "B", "other", 0.6,
                                           {"api": "hn.algolia.com", "query": "AI",
                                            "window": "2024-10-27/2026-10-28"})
                raw = collect_hackernews()
                stats["hackernews"] = ingest_archive_items(db, src, raw)[0]
            except Exception as e:
                log.exception("hackernews failed")
                errors.append(f"hackernews: {e}")
                db.rollback()

        # --- 3. Open Library --------------------------------------------
        if only in ("all", "ol", "openlibrary"):
            try:
                src = get_or_create_source(db, "openlibrary-ai", "openlibrary", "A", "other", 0.5,
                                           {"queries": ["artificial intelligence",
                                                        "machine learning",
                                                        "large language models",
                                                        "generative ai",
                                                        "deep learning"]})
                raw = collect_openlibrary(queries=["artificial intelligence",
                                                   "machine learning",
                                                   "large language models",
                                                   "generative ai",
                                                   "deep learning"])
                stats["openlibrary"] = ingest_archive_items(db, src, raw)[0]
            except Exception as e:
                log.exception("openlibrary failed")
                errors.append(f"openlibrary: {e}")
                db.rollback()

        # --- 4. Semantic Scholar (best-effort) ---------------------------
        if only in ("all", "s2", "semanticscholar"):
            try:
                src = get_or_create_source(db, "semanticscholar-ai", "semanticscholar", "A", "other", 0.7,
                                           {"queries": ["large language model",
                                                        "artificial intelligence",
                                                        "generative ai"]})
                raw = collect_semanticscholar(queries=["large language model",
                                                       "artificial intelligence",
                                                       "generative ai"])
                stats["semanticscholar"] = ingest_archive_items(db, src, raw)[0]
            except Exception as e:
                log.exception("semanticscholar failed")
                errors.append(f"semanticscholar: {e}")
                db.rollback()

        # --- 5. RSS feeds -------------------------------------------------
        if only in ("all", "rss"):
            try:
                rss_out = collect_rss_feeds()
                rss_total = 0
                for name, raw in rss_out.items():
                    src = db.execute(select(Source).where(Source.name == name)).scalar()
                    if src is None:
                        continue
                    n, _ = ingest_archive_items(db, src, raw)
                    rss_total += n
                stats["rss"] = rss_total
            except Exception as e:
                log.exception("rss failed")
                errors.append(f"rss: {e}")
                db.rollback()

        after = db.execute(text("SELECT count(*) FROM items")).scalar()

        # per item_type breakdown
        by_type = dict(db.execute(
            text("SELECT item_type, count(*) FROM items GROUP BY item_type")
        ).fetchall())
        by_source = dict(db.execute(
            text("SELECT s.name, count(i.id) FROM sources s LEFT JOIN items i ON i.source_id = s.id GROUP BY s.name")
        ).fetchall())

        log.info("=" * 60)
        log.info("DONE. new items per source: %s", stats)
        log.info("items: %d -> %d (+%d)", before, after, after - before)
        log.info("by item_type: %s", by_type)
        log.info("errors: %s", errors or "none")

        print()
        print("=" * 60)
        print(f"SOURCE STATS: {stats}")
        print(f"ITEMS: {before} -> {after}  (+{after - before})")
        print(f"BY TYPE: {by_type}")
        print(f"BY SOURCE: {by_source}")
        print(f"ERRORS: {errors or 'none'}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
