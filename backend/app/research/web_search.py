"""AI Sentinel — web search layer (SearXNG / Tavily / Brave)."""
import logging

import httpx

from app.config import settings

log = logging.getLogger("ai_sentinel.search")


def web_search(query: str, limit: int = 8) -> list[dict]:
    """Search the live web. Returns [{title, url, snippet}]."""
    provider = settings.web_search_provider
    try:
        if provider == "searxng":
            return _searxng(query, limit)
        if provider == "tavily":
            return _tavily(query, limit)
        if provider == "brave":
            return _brave(query, limit)
    except Exception as e:
        log.error("web search failed (%s): %s", provider, e)
    return []


def _searxng(query: str, limit: int) -> list[dict]:
    resp = httpx.get(
        f"{settings.searxng_url}/search",
        params={"q": query, "format": "json", "language": "en"},
        timeout=20,
    )
    resp.raise_for_status()
    out = []
    for r in resp.json().get("results", [])[:limit]:
        out.append({"title": r.get("title", ""), "url": r.get("url", ""),
                    "snippet": (r.get("content") or "")[:300]})
    return out


def _tavily(query: str, limit: int) -> list[dict]:
    resp = httpx.post(
        "https://api.tavily.com/search",
        json={"api_key": settings.tavily_api_key, "query": query, "max_results": limit},
        timeout=20,
    )
    resp.raise_for_status()
    out = []
    for r in resp.json().get("results", [])[:limit]:
        out.append({"title": r.get("title", ""), "url": r.get("url", ""),
                    "snippet": (r.get("content") or "")[:300]})
    return out


def _brave(query: str, limit: int) -> list[dict]:
    resp = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": limit},
        headers={"X-Subscription-Token": settings.brave_api_key},
        timeout=20,
    )
    resp.raise_for_status()
    out = []
    for r in resp.json().get("web", {}).get("results", [])[:limit]:
        out.append({"title": r.get("title", ""), "url": r.get("url", ""),
                    "snippet": (r.get("description") or "")[:300]})
    return out
