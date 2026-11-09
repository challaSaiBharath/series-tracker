import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from app import db
from app.api import audit, dashboard, data, days, dsa, health, review, skills, topics
from app.core.config import settings
from app.models import AuditEvent
from app.security import guard
from app.seed import seed_if_empty
from app.services import spaced
from app.services.detections import prune_audit
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("tracker")

# backend/app/main.py -> parents[2] is the repo root; the web UI lives in <repo>/frontend
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
is_prod = settings.environment == "production"

# Pages we serve ourselves get a strict CSP. Swagger UI (/docs) loads scripts from a CDN, so it is excluded.
CSP = (
    "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
    "script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Week 2 replaces create_all and ensure_columns with Alembic migrations.
    db.Base.metadata.create_all(db.engine)
    added = db.ensure_columns(db.engine)
    with db.SessionLocal() as session:
        info = {"event": "startup", "columns_added": added, "seeded": seed_if_empty(session),
                "reviews_backfilled": spaced.backfill(session), "audit_pruned": prune_audit(session)}
    logger.info(json.dumps(info))
    yield


# In production the interactive docs and schema are switched off (less to probe).
app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None,
    openapi_url=None if is_prod else "/openapi.json",
)


async def observe(request: Request, call_next):
    """Request ID, JSON log line, security headers, and an audit row for writes and errors."""
    request_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

    path = request.url.path
    ip = request.client.host if request.client else "unknown"
    agent = request.headers.get("user-agent", "")[:200]

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    if not path.startswith(("/docs", "/openapi.json")):
        response.headers["Content-Security-Policy"] = CSP

    logger.info(json.dumps({
        "event": "request", "request_id": request_id, "method": request.method, "path": path,
        "status": response.status_code, "ms": elapsed_ms, "ip": ip,
    }))
    if request.method not in ("GET", "HEAD", "OPTIONS") or response.status_code >= 400:
        try:
            with db.SessionLocal() as session:
                session.add(AuditEvent(request_id=request_id, method=request.method, path=path[:300],
                                       status=response.status_code, ip=ip, user_agent=agent))
                session.commit()
        except Exception:  # telemetry must never break a request
            logger.exception("audit write failed")
    return response


# add_middleware puts the newest one outermost: observe wraps guard, so blocked requests are logged too.
app.add_middleware(BaseHTTPMiddleware, dispatch=guard)
app.add_middleware(BaseHTTPMiddleware, dispatch=observe)

app.include_router(health.router)
for module in (dashboard, days, topics, skills, dsa, review, audit, data):
    app.include_router(module.router)

# Must be last: serves the web UI at "/" without shadowing the routes above.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="web")
