#!/usr/bin/env bash
# One-command start for macOS/Linux: creates a virtual environment, installs packages, runs the app.
set -e
cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements-dev.txt
echo "Open http://127.0.0.1:8000/  (Ctrl+C to stop)"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
