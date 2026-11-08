"""Backup file format (export and import). Strict limits so an import cannot be abused."""
import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.tracker import DayStatus, Difficulty, Level, Mode, TopicStatus, check_url


class ExportDay(BaseModel):
    date: dt.date
    mode: Mode
    planned_hrs: float = Field(ge=0, le=24)
    done_hrs: float = Field(ge=0, le=24)
    status: DayStatus
    notes: str = Field(default="", max_length=2000)


class ExportTopic(BaseModel):
    title: str = Field(max_length=200)
    track: str = Field(max_length=20)
    status: TopicStatus
    completed_on: dt.date | None = None
    evidence_url: str | None = None
    _url = field_validator("evidence_url")(check_url)


class ExportSkill(BaseModel):
    name: str = Field(max_length=120)
    baseline: Level | None = None
    current: Level | None = None
    evidence_url: str | None = None
    last_reviewed: dt.date | None = None
    _url = field_validator("evidence_url")(check_url)


class ExportDsa(BaseModel):
    date: dt.date
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(default="", max_length=80)
    difficulty: Difficulty = "Easy"
    solved_alone: bool = True
    minutes: int = Field(default=0, ge=0, le=600)
    link: str | None = None
    stage: int = Field(default=0, ge=0, le=4)
    next_review: dt.date | None = None
    _url = field_validator("link")(check_url)


class ExportFile(BaseModel):
    version: Literal[1]
    exported_at: str = ""
    days: list[ExportDay] = Field(default_factory=list, max_length=400)
    topics: list[ExportTopic] = Field(default_factory=list, max_length=1000)
    skills: list[ExportSkill] = Field(default_factory=list, max_length=200)
    dsa: list[ExportDsa] = Field(default_factory=list, max_length=2000)
