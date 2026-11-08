import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import DsaProblem
from app.schemas.tracker import DsaCreate, DsaOut, ReviewIn
from app.services.spaced import apply_review, first_review

router = APIRouter(prefix="/api/dsa", tags=["dsa"])


@router.get("", response_model=list[DsaOut])
def list_problems(limit: int = Query(default=200, ge=1, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(DsaProblem).order_by(DsaProblem.date.desc(), DsaProblem.id.desc()).limit(limit)).all()


@router.get("/due", response_model=list[DsaOut])
def due_reviews(today: dt.date | None = None, db: Session = Depends(get_db)):
    today = today or dt.date.today()
    return db.scalars(select(DsaProblem).where(DsaProblem.next_review.is_not(None), DsaProblem.next_review <= today)
                      .order_by(DsaProblem.next_review, DsaProblem.id)).all()


@router.post("", response_model=DsaOut, status_code=201)
def create_problem(body: DsaCreate, db: Session = Depends(get_db)):
    row = DsaProblem(**body.model_dump(), stage=0, next_review=first_review(body.date, body.solved_alone))
    db.add(row)
    db.commit()
    return row


@router.post("/{problem_id}/review", response_model=DsaOut)
def review_problem(problem_id: int, body: ReviewIn, today: dt.date | None = None, db: Session = Depends(get_db)):
    row = db.get(DsaProblem, problem_id)
    if row is None:
        raise HTTPException(404, "Problem not found")
    if row.next_review is None and (row.stage or 0) >= 4:
        raise HTTPException(409, "This problem is already mastered")
    apply_review(row, body.result == "remembered", today or dt.date.today())
    db.commit()
    return row


@router.delete("/{problem_id}", status_code=204)
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    row = db.get(DsaProblem, problem_id)
    if row is None:
        raise HTTPException(404, "Problem not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)
