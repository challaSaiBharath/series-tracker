# Frontend

The web interface: plain HTML, CSS, and JavaScript (no build step).

- `index.html`: page shell
- `styles.css`: look and feel (Lumora tokens: near-white page, ink cards, burnt-orange accent, Onest font)
- `app.js`: all views (Dashboard, Timetable, Syllabus, Skills, DSA, Review, Activity, Data). It calls the backend at `/api/...`.

FastAPI serves this folder at http://127.0.0.1:8000/ , so there is nothing to install or build here.

Rules in this code: pages are drawn with `textContent` (never `innerHTML`), and there are no inline scripts or styles, because the backend sends a strict Content-Security-Policy.

Later (optional, Weeks 6-7): replace this with Next.js + Tailwind. The backend API stays the same.
