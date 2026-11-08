import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import StudyDay
from app.schemas.tracker import PlanUpdate, RangePlan, StudyDayOut, StudyDayUpdate
from app.services.plan import blocks_for, hours_for

router = APIRouter(prefix="/api/days", tags=["days"])


def _apply_mode(row: StudyDay, mode: str) -> None:
    row.mode = mode
    row.planned_hrs = hours_for(mode, row.date)
    row.study_blocks = blocks_for(mode, row.date)


@router.get("", response_model=list[StudyDayOut])
def list_days(start: dt.date | None = None, end: dt.date | None = None, week: int | None = None,
              db: Session = Depends(get_db)):
    query = select(StudyDay).order_by(StudyDay.date)
    if start:
        query = query.where(StudyDay.date >= start)
    if end:
        query = query.where(StudyDay.date <= end)
    if week is not None:
        query = query.where(StudyDay.week == week)
    return db.scalars(query).all()


@router.post("/plan-range", response_model=list[StudyDayOut])
def plan_range(body: RangePlan, db: Session = Depends(get_db)):
    """Set the mode for every day in a range, e.g. mark travel days. Topics do not move; use the catch-up list."""
    rows = db.scalars(select(StudyDay).where(StudyDay.date.between(body.start, body.end)).order_by(StudyDay.date)).all()
    if not rows:
        raise HTTPException(404, "No study days in that range")
    for row in rows:
        _apply_mode(row, body.mode)
    db.commit()
    return rows


@router.get("/{day}", response_model=StudyDayOut)
def get_day(day: dt.date, db: Session = Depends(get_db)):
    row = db.get(StudyDay, day)
    if row is None:
        raise HTTPException(404, "No study day for that date")
    return row


@router.patch("/{day}", response_model=StudyDayOut)
def update_day(day: dt.date, body: StudyDayUpdate, db: Session = Depends(get_db)):
    row = db.get(StudyDay, day)
    if row is None:
        raise HTTPException(404, "No study day for that date")
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(row, field, value)
    db.commit()
    return row


@router.patch("/{day}/plan", response_model=StudyDayOut)
def update_plan(day: dt.date, body: PlanUpdate, db: Session = Depends(get_db)):
    row = db.get(StudyDay, day)
    if row is None:
        raise HTTPException(404, "No study day for that date")
    if body.mode:
        _apply_mode(row, body.mode)
    if body.planned_hrs is not None:
        row.planned_hrs = body.planned_hrs
    db.commit()
    return row
