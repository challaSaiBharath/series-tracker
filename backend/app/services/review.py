"""Weekly review data: what was planned, what got done, and what to write about."""
import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DsaProblem, Skill, StudyDay, Topic

ANCHOR = dt.date(2026, 11, 23)  # Monday of week 1
LAST_WEEK = 32


def week_number(day: dt.date) -> int:
    return max(0, min((day - ANCHOR).days // 7 + 1, LAST_WEEK))


def week_bounds(week: int) -> tuple[dt.date, dt.date]:
    if week == 0:
        return dt.date(2026, 11, 20), dt.date(2026, 11, 22)
    start = ANCHOR + dt.timedelta(days=7 * (week - 1))
    return start, start + dt.timedelta(days=6)


def build_review(db: Session, week: int) -> dict:
    start, end = week_bounds(week)
    days = list(db.scalars(select(StudyDay).where(StudyDay.date.between(start, end)).order_by(StudyDay.date)))
    return {
        "week": week, "start": start, "end": end,
        "planned_hrs": sum(d.planned_hrs for d in days),
        "done_hrs": sum(d.done_hrs for d in days),
        "days_done": sum(1 for d in days if d.status == "Done"),
        "days": days,
        "topics_done": list(db.scalars(select(Topic).where(Topic.completed_on.between(start, end)).order_by(Topic.completed_on))),
        "dsa": list(db.scalars(select(DsaProblem).where(DsaProblem.date.between(start, end)).order_by(DsaProblem.date))),
        "skills_updated": list(db.scalars(select(Skill).where(Skill.last_reviewed.between(start, end)))),
    }
