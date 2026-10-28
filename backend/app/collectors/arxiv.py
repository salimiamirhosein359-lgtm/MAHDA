"""AI Sentinel — arXiv collector."""
import logging
import re
import urllib.parse
from datetime import datetime, timedelta

import httpx

log = logging.getLogger("ai_sentinel.collectors.arxiv")

API_URL = "http://export.arxiv.org/api/query"

CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "cs.RO", "cs.NE", "stat.ML"]


def collect(days: int = 3, max_results: int = 100) -> list[dict]:
    """Fetch recent AI papers from arXiv. Returns normalized items."""
    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    params = {
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"

    items: list[dict] = []
    try:
        resp = httpx.get(url, timeout=30, headers={"User-Agent": "ai-sentinel/0.1"})
        resp.raise_for_status()
    except Exception as e:
        log.error("arxiv fetch failed: %s", e)
        return items

    ns = {"a": "http://www.w3.org/2005/Atom"}
    import lxml.etree as etree

    root = etree.fromstring(resp.content)
    cutoff = datetime.utcnow() - timedelta(days=days)

    for entry in root.findall("a:entry", ns):
        published_raw = entry.findtext("a:published", default="", namespaces=ns)
        if not published_raw:
            continue
        published = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        if published < cutoff:
            continue

        arxiv_id_el = entry.find("a:id", ns)
        arxiv_url = arxiv_id_el.text if arxiv_id_el is not None else ""
        m = re.search(r"abs/([^v]+)", arxiv_url)
        external_id = f"arxiv:{m.group(1)}" if m else arxiv_url

        summary = " ".join((entry.findtext("a:summary", default="", namespaces=ns)).split())

        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]

        items.append(
            {
                "external_id": external_id,
                "title": " ".join(entry.findtext("a:title", default="", namespaces=ns).split()),
                "url": arxiv_url,
                "summary": summary,
                "author": ", ".join(authors[:5]),
                "published_at": published,
                "item_type": "paper",
                "meta": {"categories": CATEGORIES},
            }
        )
    log.info("arxiv: %d items", len(items))
    return items
