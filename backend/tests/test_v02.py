import datetime as dt

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app import db
from app.models import AuditEvent, DsaProblem, Topic
from app.services.detections import utcnow


# ---------- security guard ----------
def test_unknown_host_is_refused(client):
    r = client.get("/health", headers={"host": "evil.example"})
    assert r.status_code == 421
    assert client.get("/health", headers={"host": "localhost:8000"}).status_code == 200
    assert client.get("/health", headers={"host": "[::1]:8000"}).status_code == 200


def test_cross_origin_writes_are_blocked(client):
    url = "/api/days/2026-11-23"
    assert client.patch(url, json={"done_hrs": 1}, headers={"origin": "http://evil.example"}).status_code == 403
    assert client.patch(url, json={"done_hrs": 1}, headers={"origin": "http://localhost:3000"}).status_code == 403
    assert client.patch(url, json={"done_hrs": 1}, headers={"origin": "null"}).status_code == 403
    assert client.patch(url, json={"done_hrs": 1}, headers={"sec-fetch-site": "cross-site"}).status_code == 403
    assert client.patch(url, json={"done_hrs": 1}, headers={"sec-fetch-site": "same-site"}).status_code == 403
    assert client.patch(url, json={"done_hrs": 1}, headers={"origin": "http://localhost", "sec-fetch-site": "same-origin"}).status_code == 200
    # reads and non-browser clients are unaffected
    assert client.get("/api/skills", headers={"origin": "http://evil.example"}).status_code == 200
    assert client.patch(url, json={"done_hrs": 2}).status_code == 200


def test_blocked_requests_are_audited_and_detected(client):
    client.get("/health", headers={"host": "evil.example"})
    client.patch("/api/days/2026-11-23", json={"done_hrs": 1}, headers={"origin": "http://evil.example"})
    events = client.get("/api/audit", params={"kind": "errors"}).json()
    assert {e["status"] for e in events} >= {421, 403}
    rules = {a["rule"] for a in client.get("/api/detections").json()}
    assert "blocked-host-or-origin" in rules
    assert client.get("/api/audit/stats").json()["blocked_24h"] >= 2


# ---------- plan editing ----------
def test_plan_mode_changes_hours_and_text(client):
    r = client.patch("/api/days/2026-11-24/plan", json={"mode": "Travel"})
    assert r.status_code == 200
    assert r.json()["mode"] == "Travel" and r.json()["planned_hrs"] == 0 and "Travel" in r.json()["study_blocks"]
    r = client.patch("/api/days/2026-11-24/plan", json={"mode": "Semester"})
    assert r.json()["planned_hrs"] == 2.5  # a Tuesday
    r = client.patch("/api/days/2026-11-28/plan", json={"mode": "Semester"})
    assert r.json()["planned_hrs"] == 4  # a Saturday
    assert client.patch("/api/days/2026-11-24/plan", json={"planned_hrs": 1.5}).json()["planned_hrs"] == 1.5
    assert client.patch("/api/days/2026-11-24/plan", json={"mode": "Holiday"}).status_code == 422
    assert client.patch("/api/days/2026-11-24/plan", json={"planned_hrs": 30}).status_code == 422
    assert client.patch("/api/days/2030-01-01/plan", json={"mode": "Travel"}).status_code == 404


def test_plan_range(client):
    r = client.post("/api/days/plan-range", json={"start": "2026-11-24", "end": "2026-11-26", "mode": "Travel"})
    assert r.status_code == 200 and [d["mode"] for d in r.json()] == ["Travel"] * 3
    assert all(d["planned_hrs"] == 0 for d in r.json())
    bad = client.post("/api/days/plan-range", json={"start": "2026-11-26", "end": "2026-11-24", "mode": "Travel"})
    assert bad.status_code == 422
    assert client.post("/api/days/plan-range", json={"start": "2030-01-01", "end": "2030-01-02", "mode": "Travel"}).status_code == 404


# ---------- dashboard: grace streak, consistency, catch-up ----------
def test_streak_forgives_one_miss_per_week(client):
    for day in ("2026-11-23", "2026-11-25", "2026-11-26"):  # Tue 24th missed
        client.patch(f"/api/days/{day}", json={"done_hrs": 2})
    body = client.get("/api/dashboard", params={"today": "2026-11-26"}).json()
    assert body["streak"] == 3  # 26, 25, (24 forgiven), 23


def test_streak_breaks_on_second_miss_in_a_week(client):
    for day in ("2026-11-23", "2026-11-26"):  # 24th and 25th missed
        client.patch(f"/api/days/{day}", json={"done_hrs": 2})
    assert client.get("/api/dashboard", params={"today": "2026-11-26"}).json()["streak"] == 1


def test_consistency_and_catch_up(client):
    client.patch("/api/days/2026-11-23", json={"done_hrs": 3, "status": "Done"})
    client.patch("/api/days/2026-11-24", json={"status": "Skipped"})
    body = client.get("/api/dashboard", params={"today": "2026-11-26"}).json()
    # planned days up to yesterday: 22nd(Prep), 23, 24, 25 -> only the 23rd has activity
    assert body["consistency_14"] == 25
    missed = {d["date"] for d in body["catch_up"]}
    assert "2026-11-24" not in missed  # skipped on purpose
    assert {"2026-11-22", "2026-11-25"} <= missed and body["catch_up_count"] == len(missed)


def test_skills_average_compares_the_same_skills(client):
    skill = client.get("/api/skills").json()[0]
    client.patch(f"/api/skills/{skill['id']}", json={"current": 1, "evidence_url": "https://github.com/me/r"})
    skills = client.get("/api/dashboard", params={"today": "2026-11-26"}).json()["skills"]
    assert skills["avg_current"] == 1 and skills["avg_target"] == 4  # only the rated skill, its own target


# ---------- spaced repetition ----------
def _add(client, **extra):
    body = {"date": "2026-11-23", "title": "Two Sum", "topic": "Hashing", **extra}
    return client.post("/api/dsa", json=body).json()


def test_first_review_is_sooner_when_help_was_needed(client):
    assert _add(client, solved_alone=True)["next_review"] == "2026-11-26"
    assert _add(client, title="Needed help", solved_alone=False)["next_review"] == "2026-11-24"


def test_review_ladder_and_mastery(client):
    pid = _add(client)["id"]
    today = dt.date(2026, 12, 1)
    expected = [(1, "2026-12-08"), (2, "2026-12-15"), (3, "2026-12-31")]
    for stage, next_date in expected:
        r = client.post(f"/api/dsa/{pid}/review", params={"today": str(today)}, json={"result": "remembered"}).json()
        assert r["stage"] == stage and r["next_review"] == next_date
    r = client.post(f"/api/dsa/{pid}/review", params={"today": str(today)}, json={"result": "remembered"}).json()
    assert r["stage"] == 4 and r["next_review"] is None and r["mastered"] is True
    assert client.post(f"/api/dsa/{pid}/review", json={"result": "remembered"}).status_code == 409
    assert client.post(f"/api/dsa/{pid}/review", json={"result": "maybe"}).status_code == 422


def test_struggled_review_restarts_the_ladder_and_due_list(client):
    pid = _add(client)["id"]
    client.post(f"/api/dsa/{pid}/review", params={"today": "2026-12-01"}, json={"result": "remembered"})
    r = client.post(f"/api/dsa/{pid}/review", params={"today": "2026-12-08"}, json={"result": "struggled"}).json()
    assert r["stage"] == 0 and r["next_review"] == "2026-12-09"
    assert client.get("/api/dsa/due", params={"today": "2026-12-08"}).json() == []
    assert [p["id"] for p in client.get("/api/dsa/due", params={"today": "2026-12-09"}).json()] == [pid]
    assert client.get("/api/dashboard", params={"today": "2026-12-09"}).json()["reviews_due"] == 1
    assert client.post("/api/dsa/9999/review", json={"result": "remembered"}).status_code == 404


# ---------- topics ----------
def test_topic_scopes_and_summary(client):
    due = client.get("/api/topics", params={"scope": "due", "today": "2026-11-26"}).json()
    assert [t["title"] for t in due] == ["HTTP and REST", "Hash maps"]
    assert client.get("/api/topics", params={"scope": "upcoming", "today": "2026-11-25"}).json()[0]["title"] == "Hash maps"
    topic_id = due[0]["id"]
    client.patch(f"/api/topics/{topic_id}", json={"status": "Done"})
    assert [t["title"] for t in client.get("/api/topics", params={"scope": "due", "today": "2026-11-26"}).json()] == ["Hash maps"]
    assert len(client.get("/api/topics", params={"scope": "done"}).json()) == 1
    summary = {e["track"]: e for e in client.get("/api/topics/summary").json()}
    assert summary["Backend"] == {"track": "Backend", "done": 1, "total": 1}
    assert summary["DSA"]["done"] == 0
    assert client.get("/api/topics", params={"scope": "nonsense"}).status_code == 422


# ---------- weekly review ----------
def test_weekly_review(client):
    client.patch("/api/days/2026-11-23", json={"done_hrs": 5, "status": "Done", "notes": "learned venvs"})
    client.post("/api/dsa", json={"date": "2026-11-24", "title": "Valid Anagram"})
    with db.SessionLocal() as s:
        s.get(Topic, 1).completed_on = dt.date(2026, 11, 25)
        s.commit()
    review = client.get("/api/review", params={"week": 1}).json()
    assert review["start"] == "2026-11-23" and review["end"] == "2026-11-29"
    assert review["done_hrs"] == 5 and review["planned_hrs"] == 6.5 * 7 and review["days_done"] == 1
    assert [t["title"] for t in review["topics_done"]] == ["HTTP and REST"]
    assert [p["title"] for p in review["dsa"]] == ["Valid Anagram"]
    assert client.get("/api/review", params={"today": "2026-12-01"}).json()["week"] == 2
    assert client.get("/api/review", params={"week": 99}).status_code == 422


# ---------- detections ----------
def _event(session, ip="1.2.3.4", path="/x", status=404, method="GET", minutes_ago=1):
    session.add(AuditEvent(ts=utcnow() - dt.timedelta(minutes=minutes_ago), request_id="t", method=method,
                           path=path, status=status, ip=ip, user_agent=""))


def test_probing_and_sensitive_path_rules(client):
    with db.SessionLocal() as s:
        for i in range(25):
            _event(s, path=f"/nope{i}")
        _event(s, ip="9.9.9.9", path="/.env")
        s.commit()
    alerts = {a["rule"]: a for a in client.get("/api/detections").json()}
    assert alerts["probing-404-405"]["ip"] == "1.2.3.4" and alerts["probing-404-405"]["count"] >= 25
    assert alerts["sensitive-paths"]["ip"] == "9.9.9.9" and alerts["sensitive-paths"]["attack"].startswith("T1190")


def test_quiet_traffic_raises_no_alerts(client):
    with db.SessionLocal() as s:
        for i in range(5):
            _event(s, path=f"/nope{i}")
        s.commit()
    assert client.get("/api/detections").json() == []


def test_new_ip_write_needs_a_baseline(client):
    with db.SessionLocal() as s:
        _event(s, ip="127.0.0.1", status=200, minutes_ago=60 * 24 * 5)  # older baseline from a known IP
        _event(s, ip="8.8.8.8", status=200, method="PATCH", path="/api/days/2026-11-23")
        s.commit()
    rules = [a["rule"] for a in client.get("/api/detections").json()]
    assert rules == ["new-ip-write"]


# ---------- backup ----------
def test_export_import_roundtrip(client):
    client.patch("/api/days/2026-11-23", json={"done_hrs": 4, "status": "Done", "notes": "n"})
    client.patch("/api/topics/1", json={"status": "Done", "evidence_url": "https://github.com/me/r"})
    client.post("/api/dsa", json={"date": "2026-11-23", "title": "Two Sum"})
    export = client.get("/api/data/export")
    assert export.status_code == 200 and "attachment" in export.headers["content-disposition"]
    backup = export.json()
    assert backup["version"] == 1 and backup["dsa"][0]["title"] == "Two Sum"

    client.patch("/api/days/2026-11-23", json={"done_hrs": 0, "status": "Not started", "notes": ""})
    client.patch("/api/topics/1", json={"status": "Not started"})
    client.delete("/api/dsa/1")
    result = client.post("/api/data/import", json=backup)
    assert result.status_code == 200 and result.json()["imported"]["dsa"] == 1
    day = client.get("/api/days/2026-11-23").json()
    assert day["done_hrs"] == 4 and day["status"] == "Done" and day["notes"] == "n"
    assert client.get("/api/topics", params={"scope": "done"}).json()[0]["evidence_url"] == "https://github.com/me/r"
    assert [p["title"] for p in client.get("/api/dsa").json()] == ["Two Sum"]


def test_import_rejects_bad_files(client):
    good = client.get("/api/data/export").json()
    assert client.post("/api/data/import", json={**good, "version": 2}).status_code == 422
    bad_url = {**good, "topics": [{"title": "x", "track": "DSA", "status": "Done", "evidence_url": "javascript:alert(1)"}]}
    assert client.post("/api/data/import", json=bad_url).status_code == 422
    too_many = {**good, "dsa": [{"date": "2026-11-23", "title": "t"}] * 2001}
    assert client.post("/api/data/import", json=too_many).status_code == 422


# ---------- schema upgrade for v0.1 databases ----------
def test_ensure_columns_upgrades_an_old_database():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE dsa_problems (id INTEGER PRIMARY KEY, date DATE, title VARCHAR(200), "
                          "topic VARCHAR(80), difficulty VARCHAR(10), solved_alone BOOLEAN, minutes INTEGER, link VARCHAR(500))"))
        conn.execute(text("INSERT INTO dsa_problems (date, title, topic, difficulty, solved_alone, minutes) "
                          "VALUES ('2026-11-23', 'Old problem', 'x', 'Easy', 1, 5)"))
    assert db.ensure_columns(engine) == ["dsa_problems.stage", "dsa_problems.next_review"]
    assert db.ensure_columns(engine) == []  # safe to run again
    from sqlalchemy.orm import sessionmaker

    from app.services import spaced
    with sessionmaker(bind=engine)() as s:
        assert spaced.backfill(s) == 1
        row = s.query(DsaProblem).one()
        assert row.stage == 0 and row.next_review == dt.date(2026, 11, 26)
