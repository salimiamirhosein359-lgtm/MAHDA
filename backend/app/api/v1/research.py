"""AI Sentinel — /research endpoints: deep-research jobs."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ResearchJob
from app.schemas import ResearchIn, ResearchJobOut

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchJobOut)
def start_research(
    payload: ResearchIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ResearchJobOut:
    """Start a deep-research job (iterative loop). Runs in background."""
    job = ResearchJob(
        question=payload.question,
        mode=payload.mode,
        breadth=payload.breadth,
        depth=payload.depth,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Import here to avoid circular imports at module load
    from app.research.deep_research import run_research_job

    background_tasks.add_task(run_research_job, job.id)
    return ResearchJobOut.model_validate(job)


@router.get("", response_model=list[ResearchJobOut])
def list_research(db: Session = Depends(get_db)) -> list[ResearchJobOut]:
    jobs = db.execute(select(ResearchJob).order_by(ResearchJob.id.desc()).limit(50)).scalars().all()
    return [ResearchJobOut.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=ResearchJobOut)
def get_research(job_id: int, db: Session = Depends(get_db)) -> ResearchJobOut:
    job = db.get(ResearchJob, job_id)
    if job is None:
        raise HTTPException(404, "research job not found")
    return ResearchJobOut.model_validate(job)
