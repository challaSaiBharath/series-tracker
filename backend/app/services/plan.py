"""Modes, their planned hours, and the text for a day's study blocks."""
import datetime as dt

# (Mon-Fri, Saturday, Sunday) planned hours per mode
MODE_HOURS = {
    "Prep": (3, 3, 3), "Heavy": (6.5, 6, 3), "Boost": (5, 6, 3), "Semester": (2.5, 4, 3.5),
    "Light": (1.5, 2, 3), "Exam pause": (0, 0, 0), "Travel": (0, 0, 0),
}


def hours_for(mode: str, day: dt.date) -> float:
    weekday = day.weekday()
    return float(MODE_HOURS[mode][0 if weekday < 5 else (1 if weekday == 5 else 2)])


def blocks_for(mode: str, day: dt.date) -> str:
    wd = day.weekday()
    if mode == "Prep":
        return "Setup tasks (3h)"
    if mode == "Travel":
        return "Travel - no study planned (optional: 30 min DSA)"
    if mode == "Exam pause":
        return "Exams only - no series work"
    if mode == "Heavy":
        if wd < 5:
            return "08:00-09:30 DSA | 09:45-12:00 Backend | 14:00-15:15 CS | 15:30-16:15 AI-tool drill | 20:00-20:45 Communication"
        return "Project 6h (2 x 3h sessions)" if wd == 5 else "Weekly review 1h + Project 2h"
    if mode == "Boost":
        if wd < 5:
            return "08:00-09:00 DSA | 09:15-11:15 Backend | 14:00-15:00 CS | 15:15-15:45 AI-tool drill | 20:00-20:30 Communication"
        return "Project 6h" if wd == 5 else "Project 2h30m + weekly review 30m"
    if mode == "Light":
        return "Light day: DSA 45m + 45m reading" if wd < 5 else "Project 2h (light)"
    # Semester
    return {
        0: "DSA 45m + Backend 105m", 1: "DSA 45m + CS 75m + AI-tool drill 30m",
        2: "DSA 45m + Backend 105m", 3: "DSA 45m + CS 75m + Communication 30m",
        4: "DSA 45m + Backend 75m + Weekly post 30m", 5: "Project 4h", 6: "Weekly review 30m + Project 3h",
    }[wd]
