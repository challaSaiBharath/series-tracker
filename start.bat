@echo off
cd /d "%~dp0backend"
if not exist .venv\Scripts\python.exe python -m venv .venv
call .venv\Scripts\activate
pip install -q -r requirements-dev.txt
echo Open http://127.0.0.1:8000/  (Ctrl+C to stop)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
