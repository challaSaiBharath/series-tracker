def test_dashboard_before_start(client):
    body = client.get("/api/dashboard", params={"today": "2026-11-08"}).json()
    assert body["days_until_start"] == 14  # series_start is Nov 22 in the test data
    assert body["today_plan"] is None
    assert body["streak"] == 0


def test_update_day_and_week_totals(client):
    r = client.patch("/api/days/2026-11-23", json={"done_hrs": 5, "status": "Done", "notes": "good day"})
    assert r.status_code == 200 and r.json()["done_hrs"] == 5
    week = client.get("/api/dashboard", params={"today": "2026-11-24"}).json()["week"]
    assert week["done_hrs"] == 5 and week["planned_hrs"] == 6.5 * 7


def test_streak_skips_pause_days_and_empty_today(client):
    for day in ("2026-11-23", "2026-11-24"):
        client.patch(f"/api/days/{day}", json={"done_hrs": 3})
    body = client.get("/api/dashboard", params={"today": "2026-11-25"}).json()
    assert body["streak"] == 2  # today (Nov 25) is empty but does not break it
    assert client.get("/api/dashboard", params={"today": "2026-11-27"}).json()["streak"] == 0


def test_day_validation(client):
    assert client.patch("/api/days/2026-11-23", json={"done_hrs": 30}).status_code == 422
    assert client.patch("/api/days/2026-11-23", json={"status": "Finished"}).status_code == 422
    assert client.patch("/api/days/2030-01-01", json={"done_hrs": 1}).status_code == 404


def test_topic_done_sets_completed_date_and_filters(client):
    topics = client.get("/api/topics", params={"track": "DSA"}).json()
    assert [t["title"] for t in topics] == ["Hash maps"]
    r = client.patch(f"/api/topics/{topics[0]['id']}", json={"status": "Done"})
    assert r.json()["completed_on"] is not None
    assert len(client.get("/api/topics", params={"status": "Done"}).json()) == 1


def test_evidence_url_must_be_http(client):
    topic_id = client.get("/api/topics").json()[0]["id"]
    bad = client.patch(f"/api/topics/{topic_id}", json={"evidence_url": "javascript:alert(1)"})
    assert bad.status_code == 422
    ok = client.patch(f"/api/topics/{topic_id}", json={"evidence_url": "https://github.com/me/repo/commit/abc"})
    assert ok.status_code == 200


def test_skill_level_needs_evidence_to_rise(client):
    skill_id = client.get("/api/skills").json()[0]["id"]
    assert client.patch(f"/api/skills/{skill_id}", json={"baseline": 1, "current": 1}).status_code == 422
    ok = client.patch(f"/api/skills/{skill_id}", json={"baseline": 1, "current": 1,
                                                       "evidence_url": "https://github.com/me/repo"})
    assert ok.status_code == 200 and ok.json()["current"] == 1
    assert client.patch(f"/api/skills/{skill_id}", json={"current": 7, "evidence_url": "https://x.io"}).status_code == 422
    # lowering a level needs no evidence
    assert client.patch(f"/api/skills/{skill_id}", json={"current": 0}).status_code == 200


def test_dsa_create_and_delete(client):
    created = client.post("/api/dsa", json={"date": "2026-11-23", "title": "Two Sum", "topic": "Hashing",
                                            "difficulty": "Easy", "minutes": 20})
    assert created.status_code == 201
    body = created.json()
    assert body["stage"] == 0 and body["next_review"] == "2026-11-26" and body["mastered"] is False
    assert client.post("/api/dsa", json={"date": "2026-11-23", "title": ""}).status_code == 422
    assert client.delete(f"/api/dsa/{body['id']}").status_code == 204
    assert client.delete(f"/api/dsa/{body['id']}").status_code == 404
    assert client.get("/api/dsa").json() == []


def test_audit_records_writes_and_errors(client):
    client.get("/api/skills")  # reads are not audited
    client.patch("/api/days/2026-11-23", json={"done_hrs": 1})
    client.get("/api/nothing-here")
    events = client.get("/api/audit").json()
    pairs = {(e["method"], e["path"], e["status"]) for e in events}
    assert ("PATCH", "/api/days/2026-11-23", 200) in pairs
    assert ("GET", "/api/nothing-here", 404) in pairs
    assert not any(e["path"] == "/api/skills" for e in events)


def test_security_headers_and_request_id(client):
    r = client.get("/health")
    assert r.json() == {"status": "ok"}
    assert r.headers["x-request-id"] and r.headers["x-content-type-options"] == "nosniff"
    assert "default-src 'self'" in r.headers["content-security-policy"]
