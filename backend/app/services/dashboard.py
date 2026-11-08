"""Numbers for the dashboard. Pure reading and arithmetic, no HTTP in here."""
import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DsaProblem, Skill, StudyDay, Topic

DSA_TARGET = 150  # matches the size of the NeetCode 150 list


def _has_activity(day: StudyDay) -> bool:
    return day.done_hrs > 0 or day.status in ("Done", "Partial")


def compute_streak(days: list[StudyDay], today: dt.date) -> int:
    """Active study days in a row, newest first. Days with 0 planned hours (exam pause, travel) are skipped.
    Today does not break it while still empty. One missed day per Mon-Sun week is forgiven (a grace day),
    so a single bad day does not erase your progress."""
    streak = 0
    grace_used: set[tuple[int, int]] = set()
    for day in sorted((d for d in days if d.date <= today), key=lambda d: d.date, reverse=True):
        if day.planned_hrs == 0:
            continue
        if _has_activity(day):
            streak += 1
            continue
        if day.date == today:
            continue
        week_key = day.date.isocalendar()[:2]
        if week_key in grace_used:
            break
        grace_used.add(week_key)
    return streak


def consistency(days: list[StudyDay], today: dt.date, window: int = 14) -> int | None:
    """Share of planned study days with activity over the last `window` days. It never resets to zero.
    Today only counts once it has activity."""
    start = today - dt.timedelta(days=window - 1)
    planned = [d for d in days if start <= d.date <= today and d.planned_hrs > 0 and (d.date < today or _has_activity(d))]
    if not planned:
        return None
    return round(100 * sum(1 for d in planned if _has_activity(d)) / len(planned))


def build_dashboard(db: Session, today: dt.date) -> dict:
    days = list(db.scalars(select(StudyDay).order_by(StudyDay.date)))
    first = days[0].date if days else None
    last = days[-1].date if days else None
    today_row = next((d for d in days if d.date == today), None)
    upcoming = [d for d in days if d.date > today and d.planned_hrs > 0][:3]

    monday = today - dt.timedelta(days=today.weekday())
    sunday = monday + dt.timedelta(days=6)
    week_days = [d for d in days if monday <= d.date <= sunday]

    past = [d for d in days if d.date <= today]
    planned_to_date = sum(d.planned_hrs for d in past)
    done_to_date = sum(d.done_hrs for d in past)

    # Missed planned days in the last 14 days that are not done or skipped: a catch-up list, not a penalty.
    catch_start = today - dt.timedelta(days=14)
    catch_up = [d for d in days if catch_start <= d.date < today and d.planned_hrs > 0
                and d.status in ("Not started", "Partial")]

    topic_rows = db.execute(select(Topic.status, func.count()).group_by(Topic.status)).all()
    by_status = {status: count for status, count in topic_rows}

    dsa_logged = db.scalar(select(func.count()).select_from(DsaProblem)) or 0
    reviews_due = db.scalar(select(func.count()).select_from(DsaProblem).where(
        DsaProblem.next_review.is_not(None), DsaProblem.next_review <= today)) or 0
    rated = [s for s in db.scalars(select(Skill)) if s.current is not None]

    return {
        "today": today,
        "series_start": first,
        "series_end": last,
        "days_until_start": (first - today).days if first and today < first else 0,
        "today_plan": today_row,
        "upcoming": upcoming,
        "week": {"start": monday, "end": sunday, "planned_hrs": sum(d.planned_hrs for d in week_days),
                 "done_hrs": sum(d.done_hrs for d in week_days)},
        "planned_to_date": planned_to_date,
        "done_to_date": done_to_date,
        "hours_total": sum(d.done_hrs for d in days),
        "streak": compute_streak(days, today),
        "consistency_14": consistency(days, today),
        "catch_up": catch_up[-7:],
        "catch_up_count": len(catch_up),
        "reviews_due": reviews_due,
        "topics": {"done": by_status.get("Done", 0), "total": sum(by_status.values()), "by_status": by_status},
        "dsa": {"logged": dsa_logged, "target": DSA_TARGET},
        "skills": {
            "rated": len(rated),
            "total": db.scalar(select(func.count()).select_from(Skill)) or 0,
            # Both averages cover the same (rated) skills, so the comparison is fair.
            "avg_current": round(sum(s.current for s in rated) / len(rated), 2) if rated else None,
            "avg_target": round(sum(s.target for s in rated) / len(rated), 2) if rated else None,
        },
    }
