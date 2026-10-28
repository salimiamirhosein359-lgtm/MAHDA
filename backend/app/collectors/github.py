"""AI Sentinel — GitHub trending AI repos collector."""
import logging
from datetime import datetime

import httpx

log = logging.getLogger("ai_sentinel.collectors.github")

API = "https://api.github.com"


def collect(token: str | None = None, max_results: int = 30) -> list[dict]:
    """Fetch recently-created/starred AI repos via GitHub search API."""
    items: list[dict] = []
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # repos created in the last 7 days mentioning AI/LLM, sorted by stars
    query = "AI+OR+LLM+OR+agent+created:>2020-01-01&sort=stars"
    # more useful: recently pushed popular AI repos
    try:
        resp = httpx.get(
            f"{API}/search/repositories",
            params={
                "q": "artificial intelligence OR llm OR ai-agent pushed:>2025-01-01",
                "sort": "updated",
                "order": "desc",
                "per_page": max_results,
            },
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.error("github fetch failed: %s", e)
        return items

    for repo in data.get("items", []):
        items.append(
            {
                "external_id": f"gh:{repo['id']}",
                "title": repo.get("full_name", "") + " — " + (repo.get("description") or "")[:200],
                "url": repo.get("html_url", ""),
                "summary": repo.get("description") or "",
                "author": (repo.get("owner") or {}).get("login"),
                "published_at": None,
                "item_type": "release",
                "meta": {
                    "stars": repo.get("stargazers_count"),
                    "language": repo.get("language"),
                    "topics": repo.get("topics", []),
                },
            }
        )
    log.info("github: %d items", len(items))
    return items
