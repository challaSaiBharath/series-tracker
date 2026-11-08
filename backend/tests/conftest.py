import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import db
from app.models import Skill, StudyDay, Topic


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    db.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db, "SessionLocal", Session)

    with Session() as s:
        for offset in range(7):  # Mon Nov 23 .. Sun Nov 29, 2026
            day = dt.date(2026, 11, 23) + dt.timedelta(days=offset)
            s.add(StudyDay(date=day, week=1, mode="Heavy", planned_hrs=6.5))
        s.add(StudyDay(date=dt.date(2026, 11, 22), week=0, mode="Prep", planned_hrs=3))
        s.add(StudyDay(date=dt.date(2026, 11, 30), week=2, mode="Exam pause", planned_hrs=0))
        s.add(Topic(title="HTTP and REST", track="Backend", planned_date=dt.date(2026, 11, 25)))
        s.add(Topic(title="Hash maps", track="DSA", planned_date=dt.date(2026, 11, 26)))
        s.add(Skill(name="Python", track="Backend", target=4))
        s.commit()

    from app.main import app
    return TestClient(app, base_url="http://localhost")
