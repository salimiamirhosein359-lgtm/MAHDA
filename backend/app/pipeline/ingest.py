"""AI Sentinel — pipeline: AI gate → dedup → classify → score → store."""
import hashlib
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm.embeddings import embed
from app.llm.llm import CLASSIFY_SYSTEM, llm_complete
from app.models import Alert, Item, Source, UserProfile, WatchTopic
from app.pipeline.rules import (
    STRONG_GATE_KEYWORDS,
    classify_by_rules,
    strip_html,
    VALID_CATEGORIES,
    VALID_CAMPS,
)

log = logging.getLogger("ai_sentinel.pipeline")

# Cheap keyword pre-filter before LLM calls (cost control)
AI_KEYWORDS = [
    "ai", "artificial intelligence", "llm", "large language model", "gpt", "chatgpt",
    "claude", "gemini", "deepmind", "openai", "anthropic", "machine learning",
    "neural network", "transformer", "diffusion", "deep learning", "qwen", "deepseek",
    "ernie", "hunyuan", "doubao", "kimi", "moonshot", "zhipu", "glm-", "llama",
    "mistral", "grok", "copilot", "agent", "rag", "fine-tun", "gpu", "nvidia",
    "tpu", "chip", "semiconductor", "inference", "training", "benchmark", "mmlu",
    "neurips", "icml", "iclr", "arxiv", "hugging face", "multimodal", "foundation model",
]


def _is_ai_relevant(text: str) -> bool:
    """Cheap gate: keyword match first; LLM only for ambiguous cases.

    When the LLM is unavailable (``llm_complete`` returns an empty string),
    the keyword gate alone decides: hits>=2 → True, hits==0 → False,
    hits==1 → True only for strong keywords (openai/nvidia/deepseek/...).
    """
    low = text.lower()
    hits = sum(1 for kw in AI_KEYWORDS if kw in low)
    if hits >= 2:
        return True
    if hits == 0:
        return False
    # hits == 1 → ambiguous
    answer = llm_complete(f"{text[:1000]}", system="Does this concern artificial intelligence? Answer ONLY true or false.")
    if answer.strip():
        return answer.strip().lower().startswith("true")
    # LLM unavailable → fall back to keyword gate
    return any(kw in low for kw in STRONG_GATE_KEYWORDS)


def _classify(text: str, source_camp: str = "other") -> dict:
    """Classify: rule-based first, LLM refines/overrides when available.

    Returns ``{"category": str, "camp": str, "actor": str|None}``.
    - rules run first so we always have a baseline (LLM may be off);
    - if the LLM answers with a valid payload, it overrides the rules —
      but "other" LLM results never overwrite a concrete rule result;
    - camp: a non-"other" source camp always wins.
    """
    rules = classify_by_rules(text)

    category = rules["category"]
    camp = rules["camp"]
    actor = rules["actor"]

    raw = llm_complete(f"{text[:2000]}", system=CLASSIFY_SYSTEM)
    if raw.strip():
        try:
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            data = json.loads(clean)
            llm_cat = (data.get("category") or "other").strip()
            llm_camp = (data.get("camp") or "other").strip()
            if llm_cat in VALID_CATEGORIES and llm_cat != "other":
                category = llm_cat
            if llm_camp in VALID_CAMPS and llm_camp != "other":
                camp = llm_camp
            llm_actor = data.get("actor")
            if isinstance(llm_actor, str) and llm_actor.strip():
                actor = llm_actor.strip()
        except Exception:
            pass  # malformed LLM output → keep rule-based result

    if source_camp in ("US", "CN", "EU"):
        camp = source_camp

    return {"category": category, "camp": camp, "actor": actor}


def _score(item: Item, source: Source) -> tuple[float, dict]:
    """Importance score ∈ [0,1] = weighted combination."""
    parts = {}

    # source weight
    parts["source_weight"] = source.weight

    # actor weight: prominent orgs/people get a boost
    actor = (item.actor or "").lower()
    big_actors = ["openai", "anthropic", "google", "deepmind", "nvidia", "meta", "huawei",
                  "alibaba", "baidu", "bytedance", "tencent", "deepseek", "microsoft", "xai"]
    parts["actor_weight"] = 1.0 if any(b in actor for b in big_actors) else 0.5

    # recency (0..1 over 7 days)
    if item.published_at:
        age_h = (datetime.utcnow() - item.published_at).total_seconds() / 3600
        parts["recency"] = max(0.0, 1 - age_h / (24 * 7))
    else:
        parts["recency"] = 0.3

    # momentum: stars for github items
    meta = item.meta or {}
    stars = meta.get("stars")
    parts["momentum"] = min(1.0, (stars or 0) / 10000) if stars else 0.3

    score = (
        0.30 * parts["source_weight"]
        + 0.20 * parts["actor_weight"]
        + 0.20 * parts["recency"]
        + 0.15 * parts["momentum"]
        + 0.15 * 0.5  # relevance placeholder (profile-aware scoring in phase 2)
    )
    return round(min(score, 1.0), 3), parts


def _should_alert(db: Session, item: Item) -> str | None:
    """Check score threshold and watch topics."""
    if item.score is not None and item.score >= 0.8:
        return "score_threshold"
    text = f"{item.title} {item.summary or ''}".lower()
    for w in db.execute(select(WatchTopic)).scalars():
        if w.term.lower() in text:
            return "watch_topic"
    return None


def ingest_items(db: Session, source: Source, raw_items: list[dict]) -> int:
    """Dedup + gate + classify + score + store. Returns number of new items stored."""
    new_count = 0
    for raw in raw_items:
        # --- dedup ---
        exists = db.execute(
            select(Item.id).where(Item.source_id == source.id, Item.external_id == raw["external_id"])
        ).scalar()
        if exists:
            continue

        # --- HTML cleanup (RSS summaries often leak <figure><img ...> tags) ---
        if raw.get("summary"):
            raw["summary"] = strip_html(raw["summary"])

        text_for_gate = f"{raw['title']} {raw.get('summary') or ''}"

        # --- AI gate (non-AI items are stored but flagged, for stats) ---
        ai_relevant = source.group in ("A",) or _is_ai_relevant(text_for_gate)

        item = Item(
            source_id=source.id,
            external_id=raw["external_id"],
            title=raw["title"][:1000],
            url=raw["url"],
            summary=raw.get("summary"),
            author=raw.get("author"),
            published_at=raw.get("published_at"),
            item_type=raw.get("item_type", "news"),
            ai_relevant=ai_relevant,
            meta=raw.get("meta") or {},
            camp=source.camp if source.camp != "other" else "other",
        )

        if ai_relevant:
            # --- classify (rules first, LLM refines when available) ---
            cls = _classify(text_for_gate, source_camp=source.camp)
            item.category = cls["category"]
            item.actor = cls["actor"]
            if source.camp == "other":
                item.camp = cls["camp"]

            # --- embedding for RAG/novelty ---
            item.embedding = embed(text_for_gate[:4000])

            db.add(item)
            db.flush()  # get item.id before scoring/alerting

            # --- score ---
            item.score, item.score_parts = _score(item, source)

            # --- alert? ---
            reason = _should_alert(db, item)
            if reason:
                db.add(Alert(item_id=item.id, reason=reason, score=item.score))
            new_count += 1
        else:
            db.add(item)

    db.commit()
    source.last_fetched_at = datetime.utcnow()
    db.commit()
    return new_count


def run_all_collectors() -> dict:
    """Entry point for the scheduler: run every enabled collector."""
    from app.collectors import arxiv, github, rss

    db: Session = SessionLocal()
    results = {}
    try:
        sources = db.execute(select(Source).where(Source.enabled.is_(True))).scalars().all()
        for source in sources:
            try:
                if source.kind == "arxiv":
                    raw = arxiv.collect()
                elif source.kind == "github":
                    raw = github.collect()
                elif source.kind == "rss":
                    raw = rss.collect(source.config.get("url", ""), source_name=source.name)
                else:
                    continue
                results[source.name] = ingest_items(db, source, raw)
            except Exception as e:
                log.error("collector %s failed: %s", source.name, e)
                results[source.name] = -1
    finally:
        db.close()
    return results
