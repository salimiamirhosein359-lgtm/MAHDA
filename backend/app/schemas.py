"""AI Sentinel — Pydantic API schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Source ----------
class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: str
    group: str
    camp: str
    weight: float
    enabled: bool
    last_fetched_at: datetime | None


# ---------- Item ----------
class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    summary: str | None
    author: str | None
    published_at: datetime | None
    item_type: str
    category: str | None
    camp: str
    actor: str | None
    score: float | None
    source_id: int


class ItemListOut(BaseModel):
    total: int
    items: list[ItemOut]


# ---------- Rivalry (China-US) ----------
class CampStat(BaseModel):
    camp: str
    count: int
    top_items: list[ItemOut]


class RivalryOut(BaseModel):
    since: datetime
    us: CampStat
    cn: CampStat


# ---------- Trends ----------
class TrendOut(BaseModel):
    category: str | None
    keyword: str
    count: int
    momentum: float


# ---------- Research ----------
class ResearchIn(BaseModel):
    question: str = Field(min_length=3)
    mode: str = "deep"  # deep | quick
    breadth: int = Field(default=3, ge=1, le=6)
    depth: int = Field(default=2, ge=1, le=4)


class ResearchStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    step_no: int
    step_type: str
    query: str | None
    finding: str | None


class ResearchJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    mode: str
    status: str
    breadth: int
    depth: int
    result_markdown: str | None
    error: str | None
    steps: list[ResearchStepOut] = []


# ---------- Ask (RAG / online) ----------
class AskIn(BaseModel):
    question: str = Field(min_length=2)
    online: bool = False  # False = memory only (RAG), True = live web (Perplexity-style)


class AskSourceOut(BaseModel):
    ref_no: int
    title: str
    url: str
    snippet: str | None


class AskOut(BaseModel):
    answer: str
    sources: list[AskSourceOut]
    online: bool


# ---------- Files ----------
class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    status: str
    error: str | None


# ---------- Bulletin ----------
class BulletinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    period: str
    period_start: datetime
    period_end: datetime
    title: str
    body_markdown: str


# ---------- Alerts ----------
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    reason: str
    score: float
    seen: bool
    created_at: datetime


# ---------- Watch ----------
class WatchIn(BaseModel):
    term: str = Field(min_length=2)
    kind: str = "topic"


class WatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    term: str
    kind: str


# ---------- Library ----------
class LibraryIn(BaseModel):
    item_id: int | None = None
    user_file_id: int | None = None
    title: str
    note: str | None = None
    tags: list[str] = []


class LibraryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int | None
    user_file_id: int | None
    title: str
    note: str | None
    tags: list
