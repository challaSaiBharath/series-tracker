"""Detection rules run over the audit_events table (see docs/DETECTION_RULES.md).
Each rule returns alerts with an ATT&CK technique id. Thresholds are starting guesses to tune with real traffic."""
import datetime as dt
from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditEvent

SENSITIVE_PATHS = ("/.env", "/.git/", "/wp-login", "/phpmyadmin")
PROBE_THRESHOLD = 20  # 404/405 responses from one IP within 5 minutes


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


def run_detections(db: Session, now: dt.datetime | None = None, window_hours: int = 24) -> list[dict]:
    now = now or utcnow()
    since = now - dt.timedelta(hours=window_hours)
    events = list(db.scalars(select(AuditEvent).where(AuditEvent.ts >= since).order_by(AuditEvent.ts)))
    alerts: list[dict] = []

    # Rule 1: probing for missing or disallowed paths (T1190)
    buckets: dict[tuple[str, int], list[AuditEvent]] = defaultdict(list)
    for e in events:
        if e.status in (404, 405):
            buckets[(e.ip, int(e.ts.timestamp() // 300))].append(e)
    probers: dict[str, list[AuditEvent]] = defaultdict(list)
    for (ip, _), group in buckets.items():
        if len(group) >= PROBE_THRESHOLD:
            probers[ip].extend(group)
    for ip, group in probers.items():
        alerts.append({"rule": "probing-404-405", "title": "Many not-found responses from one IP", "attack": "T1190",
                       "severity": "medium", "ip": ip, "count": len(group), "last_seen": max(e.ts for e in group)})

    # Rule 2: requests for secrets or admin paths (T1190, T1552)
    hits: dict[str, list[AuditEvent]] = defaultdict(list)
    for e in events:
        if any(p in e.path.lower() for p in SENSITIVE_PATHS):
            hits[e.ip].append(e)
    for ip, group in hits.items():
        alerts.append({"rule": "sensitive-paths", "title": "Requests for secrets or admin paths", "attack": "T1190, T1552",
                       "severity": "high", "ip": ip, "count": len(group), "last_seen": max(e.ts for e in group),
                       "example": group[-1].path[:120]})

    # Rule 3: blocked Host or Origin (custom: DNS rebinding or cross-site write attempts)
    blocked = [e for e in events if e.status in (403, 421)]
    if blocked:
        alerts.append({"rule": "blocked-host-or-origin", "title": "Requests blocked by the Host/Origin guard",
                       "attack": "T1189", "severity": "high", "ip": ", ".join(sorted({e.ip for e in blocked})[:3]),
                       "count": len(blocked), "last_seen": max(e.ts for e in blocked)})

    # Rule 4: successful write from an IP never seen before (custom, needs a baseline from another IP)
    first_seen = dict(db.execute(select(AuditEvent.ip, func.min(AuditEvent.ts)).group_by(AuditEvent.ip)).all())
    has_older_baseline = any(ts < since for ts in first_seen.values())
    if has_older_baseline:
        writes = Counter(e.ip for e in events if e.method not in ("GET", "HEAD", "OPTIONS") and e.status < 400
                         and first_seen.get(e.ip, since) >= since)
        for ip, count in writes.items():
            alerts.append({"rule": "new-ip-write", "title": "Write from a new IP address", "attack": "T1078",
                           "severity": "medium", "ip": ip, "count": count, "last_seen": max(
                               e.ts for e in events if e.ip == ip)})
    return alerts


def prune_audit(db: Session, keep_days: int = 90) -> int:
    cutoff = utcnow() - dt.timedelta(days=keep_days)
    rows = db.scalars(select(AuditEvent).where(AuditEvent.ts < cutoff)).all()
    for row in rows:
        db.delete(row)
    db.commit()
    return len(rows)
