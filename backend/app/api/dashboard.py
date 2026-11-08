import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.tracker import StudyDayOut
from app.services.dashboard import build_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(today: dt.date | None = None, db: Session = Depends(get_db)):
    """`today` is optional and only useful for testing or looking at another date."""
    data = build_dashboard(db, today or dt.date.today())
    if data["today_plan"] is not None:
        data["today_plan"] = StudyDayOut.model_validate(data["today_plan"])
    for key in ("upcoming", "catch_up"):
        data[key] = [StudyDayOut.model_validate(d) for d in data[key]]
    return data
