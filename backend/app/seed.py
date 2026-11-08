"""Load the timetable, syllabus, and skills from app/data/seed.json on first run."""
import datetime as dt
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Skill, StudyDay, Topic

SEED_FILE = Path(__file__).parent / "data" / "seed.json"


def _d(value: str | None) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def seed_if_empty(session: Session) -> bool:
    if session.scalar(select(func.count()).select_from(StudyDay)):
        return False
    data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    session.add_all(StudyDay(**{**row, "date": _d(row["date"])}) for row in data["days"])
    session.add_all(Topic(**{**row, "planned_date": _d(row["planned_date"])}) for row in data["topics"])
    session.add_all(Skill(**row) for row in data["skills"])
    session.commit()
    return True
