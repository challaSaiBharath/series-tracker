import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Skill
from app.schemas.tracker import SkillOut, SkillUpdate

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return db.scalars(select(Skill).order_by(Skill.id)).all()


@router.patch("/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: int, body: SkillUpdate, db: Session = Depends(get_db)):
    row = db.get(Skill, skill_id)
    if row is None:
        raise HTTPException(404, "Skill not found")
    data = body.model_dump(exclude_unset=True)

    # Business rule: a level only goes up with evidence sent in the same request.
    if data.get("current") is not None and data["current"] > (row.current or 0):
        if not data.get("evidence_url"):
            raise HTTPException(422, "A skill level can only go up with evidence: include an evidence_url")

    if "baseline" in data:
        row.baseline = data["baseline"]
    if "current" in data:
        row.current = data["current"]
        row.last_reviewed = dt.date.today()
    if "evidence_url" in data:
        row.evidence_url = data["evidence_url"]
    db.commit()
    return row
