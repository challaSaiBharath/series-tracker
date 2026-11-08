"""Spaced repetition for DSA problems: review after 3, 7, 14, then 30 days.
Needed help when solving -> first review after 1 day. A struggled review starts the ladder again."""
import datetime as dt

NEXT_DAYS = {1: 7, 2: 14, 3: 30}  # days until the next review, by successful reviews so far
MASTERED_AT = 4


def first_review(solved_on: dt.date, solved_alone: bool) -> dt.date:
    return solved_on + dt.timedelta(days=3 if solved_alone else 1)


def apply_review(problem, remembered: bool, today: dt.date) -> None:
    if remembered:
        problem.stage = (problem.stage or 0) + 1
        problem.next_review = None if problem.stage >= MASTERED_AT else today + dt.timedelta(days=NEXT_DAYS[problem.stage])
    else:
        problem.stage = 0
        problem.next_review = today + dt.timedelta(days=1)


def backfill(session) -> int:
    """Give problems logged before this feature existed a first review date."""
    from sqlalchemy import select

    from app.models import DsaProblem

    rows = session.scalars(select(DsaProblem).where(DsaProblem.next_review.is_(None), DsaProblem.stage.is_(None))).all()
    for row in rows:
        row.stage = 0
        row.next_review = first_review(row.date, row.solved_alone)
    session.commit()
    return len(rows)
