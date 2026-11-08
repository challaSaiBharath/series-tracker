"""Guards for a no-login app that listens on localhost.

1. Host allowlist: a web page you visit can point its own domain at 127.0.0.1 (DNS rebinding) and then talk
   to this app as if it were same-origin. Refusing unknown Host names stops that.
2. Origin / Sec-Fetch-Site check on writes: refuses cross-site POST/PATCH/DELETE from other web pages,
   including other apps running on a different localhost port.
These are defence in depth. They do not replace keeping the app on your own machine.
"""
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def hostname(value: str) -> str:
    """'Localhost:8000' -> 'localhost', '[::1]:8000' -> '[::1]'."""
    value = value.strip().lower()
    if value.startswith("["):
        end = value.find("]")
        return value[: end + 1] if end != -1 else ""
    return value.split(":", 1)[0]


def allowed_hosts() -> set[str]:
    return {hostname(h) for h in settings.allowed_hosts.split(",") if h.strip()}


async def guard(request: Request, call_next):
    host_header = request.headers.get("host", "")
    if hostname(host_header) not in allowed_hosts():
        return JSONResponse({"detail": "Host not allowed"}, status_code=421)

    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin")
        # Same origin means the Origin's host:port equals the Host header (scheme can differ behind a proxy).
        if origin and urlsplit(origin).netloc.lower() != host_header.strip().lower():
            return JSONResponse({"detail": "Cross-origin write blocked"}, status_code=403)
        fetch_site = request.headers.get("sec-fetch-site")
        if fetch_site and fetch_site not in ("same-origin", "none"):
            return JSONResponse({"detail": "Cross-site write blocked"}, status_code=403)
    return await call_next(request)
