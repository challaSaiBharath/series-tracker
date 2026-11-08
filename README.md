# Series Tracker (v0.2)

A personal web app to track my backend-engineer learning series: daily timetable, syllabus, skills, DSA log with spaced repetition, weekly review, and a dashboard. Single user, **no login**. A Tech Radar (LLM-powered backend tech news with a semantic cache) is added in Weeks 9-11.

**Stack:** FastAPI + SQLAlchemy + SQLite (PostgreSQL in Week 2), plain HTML/CSS/JS served by FastAPI. Next.js and Redis come later.

## Quick start (no Docker needed)
**Fastest:** macOS/Linux: `bash start.sh`. Windows: double-click `start.bat`. Either one creates the virtual environment, installs packages, and starts the app. Then open http://127.0.0.1:8000/ .

**Or step by step:**
1. Install Python 3.11+ and Git.
2. `cd backend`
3. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
4. `pip install -r requirements-dev.txt`
5. `uvicorn app.main:app --reload`
6. Open **http://127.0.0.1:8000/** for the app and **/docs** for the API.

First start creates `tracker.db` and loads the timetable (Nov 20, 2026 to Jun 30, 2027), 278 syllabus topics, and 29 skills from `backend/app/data/seed.json`. To start fresh, stop the server and delete `tracker.db`.

**Upgrading from v0.1:** unzip over your folder and keep your `tracker.db`. Copy it somewhere safe first. The app adds the new columns by itself on start.

Run the tests with `pytest` (from `backend/`). Turn on the secrets scan with `pre-commit install` (repo root), then run `pre-commit autoupdate` once.

## What's in the app
- **Dashboard:** today's plan with one-click "Mark done", "Minimum day" and "+0.5 h"; streak (one grace day per week); 14-day consistency; total hours; reviews due; catch-up list
- **Timetable:** each day's blocks and topics; record hours, status, notes; edit a day's mode and hours; mark a range as travel or exams; "Today" button
- **Syllabus:** progress bars per track; filters (due now, upcoming, done); search; evidence links
- **Skills:** levels 0-4 with a progress bar; a level only goes up with an evidence link
- **DSA:** log problems; reviews after 3, 7, 14, 30 days (1 day if you needed help) with Remembered / Struggled
- **Review:** weekly hours, topics finished, problems solved, notes, and a post draft to copy
- **Activity:** every write and error; four detection rules shown as alerts
- **Data:** download a JSON backup; restore from one

## Folder layout
- `frontend/`: the web UI (`index.html`, `styles.css`, `app.js`), served by the backend
- `backend/`: the API (FastAPI), database code, tests
- `plan/`: `Backend_Series_Timetable.xlsx`, your day-by-day timetable and trackers
- `start.sh`, `start.bat`: one-command start
- `backend/app/api`: routers (HTTP only)
- `backend/app/services`: logic (dashboard, spaced repetition, detections, backup, plan)
- `backend/app/models`, `schemas`: database tables; request/response shapes and validation
- `backend/app/security.py`: Host and Origin guard
- `backend/app/db.py`, `seed.py`, `core/config.py`: database, first-run data, settings
- `backend/tests`: 31 tests
- `docs/`: `SPEC.md`, `DETECTION_RULES.md`, `RESEARCH.md`, `WEEK-01.md`
- `docker-compose.yml`: PostgreSQL with pgvector, used from Week 2 (not needed yet)

## Security notes
- No login because only I use it. **Run it on your own machine only.** uvicorn listens on 127.0.0.1 by default. Before deploying (Week 15), put basic auth at Nginx and set `ALLOWED_HOSTS`.
- A Host allowlist and an Origin/Sec-Fetch-Site check refuse DNS-rebinding and cross-site write attempts. These are defence in depth, not a replacement for staying local.
- Every request gets an ID and a JSON log line. Writes and errors are saved in `audit_events` (kept 90 days) and checked by the detection rules.
- Responses carry security headers and a strict Content-Security-Policy. The UI builds pages with `textContent`, never `innerHTML`. Evidence links must start with http:// or https://. Backup imports are size-limited and validated.
- Never commit `.env` or `tracker.db`. The LLM key (Week 9+) stays on the server.

## How this fits the learning series
The app was built for you so you can track from day one. Your weekly work is to **understand and rebuild it**:
- Week 1: read every file, then rebuild a small topics API in `practice/week1_api/` (`docs/WEEK-01.md`)
- Week 2: replace SQLite with PostgreSQL, and `create_all` and `ensure_columns` with Alembic migrations
- Week 3: move queries out of the routers into repositories; expand the tests
- Week 8: Redis cache for the dashboard; scheduled review reminders
- Weeks 9-11: Tech Radar and the semantic cache
- Weeks 16-17: tune the detection rules with real traffic

Rule: write the first version of new logic yourself; use the AI tool to review, test, and explain, and read everything before committing.
