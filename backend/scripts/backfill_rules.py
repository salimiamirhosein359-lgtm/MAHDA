"""AI Sentinel — one-shot backfill: re-classify stored items with rules.

Finds every Item whose category or camp is "other" (missed because the LLM
classifier is currently offline) and re-runs the rule-based classifier over
title + summary, then prints before/after statistics.

Run from the backend folder:  python scripts/backfill_rules.py
"""
import sys
from pathlib import Path
from collections import Counter

# make `app` importable when run as `python scripts/backfill_rules.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Item, Source  # noqa: E402
from app.pipeline.rules import classify_by_rules, strip_html  # noqa: E402


def backfill() -> None:
    db = SessionLocal()
    try:
        items = db.execute(select(Item)).scalars().all()
        sources = {s.id: s for s in db.execute(select(Source)).scalars()}

        cat_before = Counter(i.category or "other" for i in items)
        camp_before = Counter(i.camp or "other" for i in items)

        updated = 0
        for it in items:
            if it.category not in (None, "other") and it.camp != "other":
                continue  # already classified
            src = sources.get(it.source_id)
            source_camp = src.camp if src else "other"

            text = f"{it.title} {it.summary or ''}"
            res = classify_by_rules(text)

            changed = False
            # category: only fill/replace when currently "other"/None
            if it.category in (None, "other") and res["category"] != "other":
                it.category = res["category"]
                changed = True
            # camp: non-"other" source camp wins; otherwise rules fill "other"
            if it.camp == "other":
                if source_camp in ("US", "CN", "EU"):
                    if it.camp != source_camp:
                        it.camp = source_camp
                        changed = True
                elif res["camp"] != "other":
                    it.camp = res["camp"]
                    changed = True
            # actor: fill only when missing
            if it.actor is None and res["actor"]:
                it.actor = res["actor"]
                changed = True
            # also clean any HTML still leaking in stored summaries
            if it.summary and ("<" in it.summary or "&#" in it.summary):
                cleaned = strip_html(it.summary)
                if cleaned != it.summary:
                    it.summary = cleaned
                    changed = True

            if changed:
                updated += 1

        db.commit()

        db.expire_all()
        items = db.execute(select(Item)).scalars().all()
        cat_after = Counter(i.category or "other" for i in items)
        camp_after = Counter(i.camp or "other" for i in items)

        print(f"total items: {len(items)}, updated: {updated}")
        print("\ncategory (before -> after):")
        for cat in sorted(set(cat_before) | set(cat_after)):
            print(f"  {cat:<16} {cat_before.get(cat, 0):>3} -> {cat_after.get(cat, 0):>3}")
        print("\ncamp (before -> after):")
        for camp in sorted(set(camp_before) | set(camp_after)):
            print(f"  {camp:<8} {camp_before.get(camp, 0):>3} -> {camp_after.get(camp, 0):>3}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
