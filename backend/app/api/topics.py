import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Topic
from app.schemas.tracker import TopicOut, TopicStatus, TopicUpdate

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(
    track: str | None = Query(default=None, max_length=20),
    status: TopicStatus | None = None,
    q: str | None = Query(default=None, max_length=100),
    scope: Literal["all", "due", "upcoming", "done"] = "all",
    today: dt.date | None = None,
    db: Session = Depends(get_db),
):
    """scope: due = planned on or before today and not done; upcoming = planned later and not done."""
    today = today or dt.date.today()
    query = select(Topic).order_by(Topic.planned_date, Topic.id)
    if track:
        query = query.where(Topic.track == track)
    if status:
        query = query.where(Topic.status == status)
    if q:
        query = query.where(Topic.title.ilike(f"%{q}%"))
    if scope == "due":
        query = query.where(Topic.planned_date <= today, Topic.status != "Done")
    elif scope == "upcoming":
        query = query.where(Topic.planned_date > today, Topic.status != "Done")
    elif scope == "done":
        query = query.where(Topic.status == "Done")
    return db.scalars(query).all()


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Done and total topics per track, for the progress bars."""
    rows = db.execute(select(Topic.track, Topic.status, func.count()).group_by(Topic.track, Topic.status)).all()
    out: dict[str, dict] = {}
    for track, status, count in rows:
        entry = out.setdefault(track, {"track": track, "done": 0, "total": 0})
        entry["total"] += count
        if status == "Done":
            entry["done"] += count
    return sorted(out.values(), key=lambda e: e["track"])


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, body: TopicUpdate, db: Session = Depends(get_db)):
    row = db.get(Topic, topic_id)
    if row is None:
        raise HTTPException(404, "Topic not found")
    data = body.model_dump(exclude_unset=True)
    if "evidence_url" in data:
        row.evidence_url = data["evidence_url"]
    if data.get("status"):
        row.status = data["status"]
        row.completed_on = dt.date.today() if row.status == "Done" else None
    db.commit()
    return row
