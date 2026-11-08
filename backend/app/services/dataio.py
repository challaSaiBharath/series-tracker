"""Backup export and import. Import updates progress fields on existing rows and replaces the DSA log."""
import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import DsaProblem, Skill, StudyDay, Topic
from app.schemas.data import ExportFile


def export_all(db: Session) -> dict:
    return {
        "version": 1,
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "days": [{"date": d.date.isoformat(), "mode": d.mode, "planned_hrs": d.planned_hrs, "done_hrs": d.done_hrs,
                  "status": d.status, "notes": d.notes} for d in db.scalars(select(StudyDay).order_by(StudyDay.date))],
        "topics": [{"title": t.title, "track": t.track, "status": t.status,
                    "completed_on": t.completed_on.isoformat() if t.completed_on else None,
                    "evidence_url": t.evidence_url} for t in db.scalars(select(Topic).order_by(Topic.id))],
        "skills": [{"name": s.name, "baseline": s.baseline, "current": s.current, "evidence_url": s.evidence_url,
                    "last_reviewed": s.last_reviewed.isoformat() if s.last_reviewed else None}
                   for s in db.scalars(select(Skill).order_by(Skill.id))],
        "dsa": [{"date": p.date.isoformat(), "title": p.title, "topic": p.topic, "difficulty": p.difficulty,
                 "solved_alone": p.solved_alone, "minutes": p.minutes, "link": p.link, "stage": p.stage or 0,
                 "next_review": p.next_review.isoformat() if p.next_review else None}
                for p in db.scalars(select(DsaProblem).order_by(DsaProblem.id))],
    }


def import_all(db: Session, data: ExportFile) -> dict:
    counts = {"days": 0, "topics": 0, "skills": 0, "dsa": len(data.dsa)}
    days = {d.date: d for d in db.scalars(select(StudyDay))}
    for item in data.days:
        row = days.get(item.date)
        if row:
            row.mode, row.planned_hrs, row.done_hrs, row.status, row.notes = (
                item.mode, item.planned_hrs, item.done_hrs, item.status, item.notes)
            counts["days"] += 1
    topics = {(t.title, t.track): t for t in db.scalars(select(Topic))}
    for item in data.topics:
        row = topics.get((item.title, item.track))
        if row:
            row.status, row.completed_on, row.evidence_url = item.status, item.completed_on, item.evidence_url
            counts["topics"] += 1
    skills = {s.name: s for s in db.scalars(select(Skill))}
    for item in data.skills:
        row = skills.get(item.name)
        if row:
            row.baseline, row.current, row.evidence_url, row.last_reviewed = (
                item.baseline, item.current, item.evidence_url, item.last_reviewed)
            counts["skills"] += 1
    db.execute(delete(DsaProblem))
    db.add_all(DsaProblem(**p.model_dump()) for p in data.dsa)
    db.commit()
    return counts
