# Series Tracker: Spec (v0)

Single-user personal app. **No login.** v0.2 is built: dashboard, timetable (with plan editing), syllabus, skills, DSA log with spaced repetition, weekly review, activity with live detection rules, and backup/restore. Runs locally until Week 15; when deployed, it is kept private with basic auth at the Nginx proxy.

## MVP features
1. Timetable: each day's mode, planned hours, done hours, status, notes
2. Syllabus and skills: topic status, skill levels 0-4, evidence links (a level only rises with evidence)
3. DSA log: problems with revisit dates (+3 and +7 days)
4. Dashboard: streak, weekly completion, hours
5. Tech Radar (Weeks 9-11): backend tech news from multiple sources, LLM summaries, relevance scores, suggestions

## Data model (draft, no users table)
| Table | Columns |
|---|---|
| `topics` | id, title, track, phase, planned_date, status, completed_on, evidence_url |
| `skills` | id, name, track, baseline, current, target, evidence_url, last_reviewed |
| `study_days` | date (PK), mode, planned_hrs, done_hrs, status, notes |
| `dsa_problems` | id, date, title, topic, difficulty, solved_alone, minutes, link, stage, next_review |
| `audit_events` | id, ts, request_id, event_type, ip, user_agent, path, status, details (JSON) |
| `radar_sources` | id, name, kind (rss / github / api), url, enabled |
| `radar_items` | id, source_id, url (unique), title, summary, relevance, embedding (vector), fetched_at |
| `radar_suggestions` | id, item_id, topic_id, text, status (new / accepted / dismissed) |
| `llm_cache` | id, prompt_hash, embedding (vector), response (JSON), model, created_at, expires_at |

## Tech Radar pipeline
1. **Fetch** from official feeds and APIs only (RSS, GitHub releases, Hacker News API, security advisories). No scraping.
2. **Store** title, link, and our own summary. Do not store full article text.
3. **Dedupe** by URL, then by embedding similarity (semantic cache #1).
4. **LLM**: summarize, score relevance against syllabus topics, return structured JSON. Reuse cached results for similar items (semantic cache #2, table `llm_cache`).
5. **Suggest**: propose topic updates. They need your approval; the Radar never edits your plan on its own.

## Security and detection notes
- Fetched news is untrusted input and may contain prompt-injection text. The LLM treats it as data only and never triggers actions.
- The LLM key lives in a server-side environment variable only.
- Postgres is bound to 127.0.0.1. API docs are off in production.
- Structured JSON logs with a request ID, plus `audit_events` rows (built in Weeks 3 and 16). Detection rules: see `DETECTION_RULES.md`.

## Build order (matches the timetable)
| Week | Build |
|---|---|
| 1 | Repo, FastAPI skeleton, /health, in-memory topics CRUD (you write this) |
| 2 | Schema, migrations, persistent CRUD |
| 3 | Validation, error handling, layers, request-ID logging, `audit_events` |
| 5-6 | Syllabus, skills, daily log, DSA log endpoints; Next.js shell |
| 8 | Redis cache for dashboard stats, background jobs, revisit scheduler |
| 9-11 | Tech Radar: sources, LLM processing, semantic cache, digest page |
| 13-15 | Docker, CI, deploy (private) |
| 16-17 | Monitoring, detection rules, hardening |
