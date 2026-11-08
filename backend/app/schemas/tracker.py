"""Request and response shapes (Pydantic). Validation happens here, before any database work."""
import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

DayStatus = Literal["Not started", "Done", "Partial", "Skipped"]
TopicStatus = Literal["Not started", "Learning", "Practiced", "Done"]
Difficulty = Literal["Easy", "Medium", "Hard"]
Level = Annotated[int, Field(ge=0, le=4)]
Mode = Literal["Prep", "Heavy", "Boost", "Semester", "Light", "Exam pause", "Travel"]


def check_url(value: str | None) -> str | None:
    """Only http(s) links are accepted, so a stored value can never be a javascript: link."""
    if value is None or value.strip() == "":
        return None
    value = value.strip()
    if len(value) > 500:
        raise ValueError("URL is too long (max 500 characters)")
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    return value


class Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StudyDayOut(Out):
    date: dt.date
    week: int
    mode: str
    phase: str
    study_blocks: str
    backend_topic: str
    dsa_topic: str
    cs_topic: str
    project_task: str
    planned_hrs: float
    done_hrs: float
    status: str
    notes: str


class StudyDayUpdate(BaseModel):
    done_hrs: float | None = Field(default=None, ge=0, le=24)
    status: DayStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)


class TopicOut(Out):
    id: int
    title: str
    track: str
    planned_date: dt.date | None
    status: str
    completed_on: dt.date | None
    evidence_url: str | None


class TopicUpdate(BaseModel):
    status: TopicStatus | None = None
    evidence_url: str | None = None

    _url = field_validator("evidence_url")(check_url)


class SkillOut(Out):
    id: int
    name: str
    track: str
    baseline: int | None
    current: int | None
    target: int
    evidence_url: str | None
    last_reviewed: dt.date | None


class SkillUpdate(BaseModel):
    baseline: Level | None = None
    current: Level | None = None
    evidence_url: str | None = None

    _url = field_validator("evidence_url")(check_url)


class DsaCreate(BaseModel):
    date: dt.date
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(default="", max_length=80)
    difficulty: Difficulty = "Easy"
    solved_alone: bool = True
    minutes: int = Field(default=0, ge=0, le=600)
    link: str | None = None

    _url = field_validator("link")(check_url)


class DsaOut(Out):
    id: int
    date: dt.date
    title: str
    topic: str
    difficulty: str
    solved_alone: bool
    minutes: int
    link: str | None
    stage: int = 0
    next_review: dt.date | None = None

    @field_validator("stage", mode="before")
    @classmethod
    def _stage_default(cls, value):
        return value or 0

    @computed_field
    @property
    def mastered(self) -> bool:
        return self.stage >= 4


class ReviewIn(BaseModel):
    result: Literal["remembered", "struggled"]


class PlanUpdate(BaseModel):
    mode: Mode | None = None
    planned_hrs: float | None = Field(default=None, ge=0, le=24)


class RangePlan(BaseModel):
    start: dt.date
    end: dt.date
    mode: Mode

    @model_validator(mode="after")
    def _check_range(self):
        if self.end < self.start:
            raise ValueError("end must not be before start")
        if (self.end - self.start).days > 400:
            raise ValueError("range is too long (max 400 days)")
        return self


class AuditOut(Out):
    id: int
    ts: dt.datetime
    request_id: str
    method: str
    path: str
    status: int
    ip: str
    user_agent: str
