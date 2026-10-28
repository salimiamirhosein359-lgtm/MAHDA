"""AI Sentinel — RSS collector (news, lab blogs, geopolitics, China-US sources)."""
import logging
from datetime import datetime

import feedparser

log = logging.getLogger("ai_sentinel.collectors.rss")


def _guid(entry) -> str:
    if getattr(entry, "id", None):
        return str(entry.id)
    return getattr(entry, "link", "") or getattr(entry, "title", "")


def collect(feed_url: str, source_name: str = "", limit: int = 50) -> list[dict]:
    """Fetch one RSS/Atom feed. Returns normalized items."""
    items: list[dict] = []
    try:
        parsed = feedparser.parse(feed_url)
    except Exception as e:
        log.error("rss fetch failed (%s): %s", feed_url, e)
        return items

    for entry in (parsed.entries or [])[:limit]:
        published = None
        for key in ("published", "updated"):
            raw = getattr(entry, key, None)
            if raw:
                try:
                    from dateutil import parser as dparser

                    published = dparser.parse(str(raw)).replace(tzinfo=None)
                except Exception:
                    pass
                break

        summary = " ".join(((getattr(entry, "summary", "") or "").split()))[:2000]
        items.append(
            {
                "external_id": f"rss:{_guid(entry)}",
                "title": getattr(entry, "title", "")[:500],
                "url": getattr(entry, "link", ""),
                "summary": summary,
                "author": getattr(entry, "author", None),
                "published_at": published,
                "item_type": "news",
                "meta": {"feed": feed_url, "source_name": source_name},
            }
        )
    log.info("rss %s: %d items", source_name or feed_url, len(items))
    return items
