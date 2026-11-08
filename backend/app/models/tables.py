"""Database tables (SQLAlchemy 2.0). Single user, so there is no user_id anywhere."""
import datetime as dt

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class StudyDay(Base):
    __tablename__ = "study_days"
    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    week: Mapped[int] = mapped_column(Integer, index=True)
    mode: Mapped[str] = mapped_column(String(20))
    phase: Mapped[str] = mapped_column(String(80), default="")
    study_blocks: Mapped[str] = mapped_column(Text, default="")
    backend_topic: Mapped[str] = mapped_column(String(200), default="-")
    dsa_topic: Mapped[str] = mapped_column(String(200), default="-")
    cs_topic: Mapped[str] = mapped_column(String(200), default="-")
    project_task: Mapped[str] = mapped_column(String(300), default="-")
    planned_hrs: Mapped[float] = mapped_column(Float, default=0)
    done_hrs: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="Not started")
    notes: Mapped[str] = mapped_column(Text, default="")


class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    track: Mapped[str] = mapped_column(String(20), index=True)
    planned_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Not started", index=True)
    completed_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    track: Mapped[str] = mapped_column(String(40))
    baseline: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target: Mapped[int] = mapped_column(Integer, default=3)
    evidence_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_reviewed: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class DsaProblem(Base):
    __tablename__ = "dsa_problems"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(200))
    topic: Mapped[str] = mapped_column(String(80), default="")
    difficulty: Mapped[str] = mapped_column(String(10), default="Easy")
    solved_alone: Mapped[bool] = mapped_column(Boolean, default=True)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Spaced repetition: number of successful reviews so far, and when the next one is due.
    stage: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    next_review: Mapped[dt.date | None] = mapped_column(Date, nullable=True, index=False)


class AuditEvent(Base):
    """Telemetry for detection: every write and every error response is recorded."""
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts: Mapped[dt.datetime] = mapped_column(DateTime, default=lambda: dt.datetime.now(dt.timezone.utc).replace(tzinfo=None), index=True)
    request_id: Mapped[str] = mapped_column(String(32))
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(300))
    status: Mapped[int] = mapped_column(Integer)
    ip: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(String(200), default="")
