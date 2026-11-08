import datetime as dt
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent
from app.schemas.tracker import AuditOut
from app.services.detections import run_detections, utcnow

router = APIRouter(prefix="/api", tags=["activity"])


@router.get("/audit", response_model=list[AuditOut])
def recent_events(limit: int = Query(default=50, ge=1, le=200), kind: Literal["all", "writes", "errors"] = "all",
                  db: Session = Depends(get_db)):
    query = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
    if kind == "writes":
        query = query.where(AuditEvent.method.not_in(("GET", "HEAD", "OPTIONS")))
    elif kind == "errors":
        query = query.where(AuditEvent.status >= 400)
    return db.scalars(query).all()


@router.get("/audit/stats")
def stats(db: Session = Depends(get_db)):
    since = utcnow() - dt.timedelta(hours=24)

    def count(*conditions):
        return db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.ts >= since, *conditions)) or 0

    return {"events_24h": count(), "writes_24h": count(AuditEvent.method.not_in(("GET", "HEAD", "OPTIONS"))),
            "errors_24h": count(AuditEvent.status >= 400), "blocked_24h": count(AuditEvent.status.in_((403, 421)))}


@router.get("/detections")
def detections(db: Session = Depends(get_db)):
    return run_detections(db)
