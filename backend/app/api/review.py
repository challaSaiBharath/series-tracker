import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.tracker import DsaOut, SkillOut, StudyDayOut, TopicOut
from app.services.review import LAST_WEEK, build_review, week_number

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("")
def weekly_review(week: int | None = Query(default=None, ge=0, le=LAST_WEEK), today: dt.date | None = None,
                  db: Session = Depends(get_db)):
    n = week if week is not None else week_number(today or dt.date.today())
    data = build_review(db, n)
    return {**data,
            "days": [StudyDayOut.model_validate(d) for d in data["days"]],
            "topics_done": [TopicOut.model_validate(t) for t in data["topics_done"]],
            "dsa": [DsaOut.model_validate(p) for p in data["dsa"]],
            "skills_updated": [SkillOut.model_validate(s) for s in data["skills_updated"]]}
