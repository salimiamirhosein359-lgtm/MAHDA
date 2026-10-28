"""AI Sentinel — SQLAlchemy models (PostgreSQL + pgvector)."""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:  # pgvector available only when running with the extension installed
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:  # pragma: no cover - fallback for tests without pgvector
    HAS_PGVECTOR = False

EMBEDDING_DIM = 384  # paraphrase-multilingual-MiniLM-L12-v2


class Base(DeclarativeBase):
    pass


def _embedding_col():
    """Vector column when pgvector is available, JSON fallback otherwise."""
    if HAS_PGVECTOR:
        return mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    return mapped_column(JSON, nullable=True)


class Source(Base):
    """A monitored source (arxiv category, RSS feed, GitHub query...)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # arxiv | rss | github | hf | ...
    config: Mapped[dict] = mapped_column(JSONB, default=dict)  # url, category, query...
    group: Mapped[str] = mapped_column(String(20), default="A")  # A | B | C | D
    camp: Mapped[str] = mapped_column(String(10), default="other")  # US | CN | EU | other
    weight: Mapped[float] = mapped_column(Float, default=0.5)  # source weight for scoring
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["Item"]] = relationship(back_populates="source")


class Item(Base):
    """Every monitored piece of content: paper, news, quote, regulation..."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(500), nullable=False)  # guid/arxiv id/url hash
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # extracted full text
    author: Mapped[str | None] = mapped_column(String(300), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    item_type: Mapped[str] = mapped_column(String(30), default="news")  # paper|news|release|quote|policy
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # taxonomy key
    camp: Mapped[str] = mapped_column(String(10), default="other")  # US | CN | EU | other
    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)  # person/org mentioned
    ai_relevant: Mapped[bool] = mapped_column(Boolean, default=True)  # AI Gate result
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_parts: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding = _embedding_col()
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["Source"] = relationship(back_populates="items")

    __table_args__ = (
        Index("ix_items_source_ext", "source_id", "external_id", unique=True),
        Index("ix_items_published", "published_at"),
        Index("ix_items_category", "category"),
        Index("ix_items_camp", "camp"),
    )


class Bulletin(Base):
    """Auto-generated digest (daily/weekly)."""

    __tablename__ = "bulletins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String(20), default="daily")  # daily | weekly
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    item_ids: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ResearchJob(Base):
    """A deep-research task."""

    __tablename__ = "research_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), default="deep")  # deep | quick
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|done|failed
    breadth: Mapped[int] = mapped_column(Integer, default=3)
    depth: Mapped[int] = mapped_column(Integer, default=2)
    result_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    steps: Mapped[list["ResearchStep"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ResearchStep(Base):
    """One step of the research loop — for transparency."""

    __tablename__ = "research_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("research_jobs.id"), nullable=False)
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)  # search|read|gap|synth
    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    finding: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources_json: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ResearchJob"] = relationship(back_populates="steps")


class ResearchSource(Base):
    """A cited online source (Perplexity-style numbered references)."""

    __tablename__ = "research_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("research_jobs.id"), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    ref_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_online: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserFile(Base):
    """User-uploaded file: pdf/word/image/audio — processed into searchable text."""

    __tablename__ = "user_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf|docx|image|audio|md
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|processing|ready|failed
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding = _embedding_col()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LibraryEntry(Base):
    """Personal library: saved items with notes and tags."""

    __tablename__ = "library_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int | None] = mapped_column(ForeignKey("items.id"), nullable=True)
    user_file_id: Mapped[int | None] = mapped_column(ForeignKey("user_files.id"), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Dashboard alerts for high-scoring items."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)  # score_threshold | watch_topic
    score: Mapped[float] = mapped_column(Float, nullable=False)
    seen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WatchTopic(Base):
    """Topics/people/companies the user tracks."""

    __tablename__ = "watch_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    term: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), default="topic")  # topic|person|company
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    """User interests profile for relevance scoring."""

    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    interests_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    alert_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    embedding = _embedding_col()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
