"""AI Sentinel — iterative deep-research loop (dzhng/deep-research pattern)."""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm.llm import llm_complete
from app.models import ResearchJob, ResearchStep
from app.research.rag import _memory_context
from app.research.web_search import web_search

log = logging.getLogger("ai_sentinel.research")

PLAN_SYSTEM = """You are a research planner. Given a question, generate a JSON array of
3-6 diverse web-search queries that together cover the question well.
Return ONLY the JSON array of strings, no prose."""

GAP_SYSTEM = """You are a research analyst. Given findings so far, list what is still
missing or uncertain to fully answer the question. Return a short bullet list or
"COMPLETE" if the findings are sufficient. Answer in Persian."""

SYNTH_SYSTEM = """You are a research report writer. Write a well-structured report in Persian
(Markdown) answering the question, using numbered citations [1], [2] to the sources.
Include: خلاصه اجرایی، یافته‌های اصلی (با ارجاع)، مقایسه/جدول در صورت نیاز، نتیجه‌گیری،
و فهرست منابع در انتها. Be factual; only use the provided findings."""


def _llm_json_list(prompt: str) -> list[str]:
    raw = llm_complete(prompt, system=PLAN_SYSTEM, temperature=0.4)
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        import json

        data = json.loads(clean)
        return [str(q) for q in data][:6]
    except Exception:
        return []


def _gather(db: Session, query: str, online: bool = True) -> list[dict]:
    """Search memory (RAG) + live web for one query."""
    results = _memory_context(db, query, k=4)
    if online:
        results += web_search(query, limit=5)
    return results


def run_research_job(job_id: int) -> None:
    """The iterative loop: plan → search → summarize → gap-check → repeat → synthesize."""
    db: Session = SessionLocal()
    try:
        job = db.get(ResearchJob, job_id)
        if job is None:
            return
        job.status = "running"
        db.commit()

        try:
            all_sources: dict[str, dict] = {}  # url → source info
            findings: list[str] = []
            step_no = 0
            queries: list[str] = []

            for depth_i in range(max(1, job.depth)):
                # ---- [1] plan queries (first iteration: initial; later: gap-driven) ----
                if not queries:
                    queries = _llm_json_list(f"Research question: {job.question}")
                    if not queries:
                        queries = [job.question]
                step_no += 1
                db.add(ResearchStep(job_id=job.id, step_no=step_no, step_type="plan",
                                   finding="; ".join(queries)))
                db.commit()

                # ---- [2] search + [4] summarize ----
                for q in queries[: job.breadth]:
                    results = _gather(db, q)
                    step_no += 1
                    db.add(ResearchStep(job_id=job.id, step_no=step_no, step_type="search", query=q))
                    for r in results:
                        all_sources.setdefault(r["url"], r)
                    if results:
                        snippet_text = "\n".join(f"- {r['title']}: {r.get('snippet', '')}" for r in results)
                        summary = llm_complete(
                            f"Query: {q}\nResults:\n{snippet_text}\n\nKey findings (Persian, bullets):",
                            temperature=0.2,
                        )
                        if summary:
                            findings.append(f"**{q}**\n{summary}")
                            step_no += 1
                            db.add(ResearchStep(job_id=job.id, step_no=step_no, step_type="read",
                                               query=q, finding=summary[:2000]))
                    db.commit()

                # ---- [5] gap analysis ----
                gap = llm_complete(
                    f"Question: {job.question}\n\nFindings so far:\n" + "\n\n".join(findings[-8:]),
                    system=GAP_SYSTEM,
                )
                step_no += 1
                db.add(ResearchStep(job_id=job.id, step_no=step_no, step_type="gap", finding=gap[:2000]))
                db.commit()

                # ---- [6] enough? ----
                if "COMPLETE" in gap.upper() or depth_i == job.depth - 1:
                    break
                queries = _llm_json_list(
                    f"Question: {job.question}\nGaps to fill:\n{gap}\n\nGenerate new search queries:"
                )

            # ---- [7] final synthesis ----
            source_list = list(all_sources.values())
            sources_text = "\n".join(
                f"[{i+1}] {s['title']}\n    {s['url']}" for i, s in enumerate(source_list)
            )
            report = llm_complete(
                f"Question: {job.question}\n\nFindings:\n" + "\n\n".join(findings)
                + f"\n\nSources:\n{sources_text}\n\nWrite the final report:",
                system=SYNTH_SYSTEM,
                max_tokens=4000,
            )
            if not report:
                report = "تولید گزارش ناموفق بود — تنظیمات LLM را بررسی کنید."

            job.result_markdown = (
                report
                + "\n\n---\n### منابع\n"
                + "\n".join(f"[{i+1}] [{s['title']}]({s['url']})" for i, s in enumerate(source_list))
            )
            job.status = "done"
            job.finished_at = datetime.utcnow()
        except Exception as e:
            log.error("research job %s failed: %s", job_id, e)
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
