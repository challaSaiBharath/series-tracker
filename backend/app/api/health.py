from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Later (Week 16) this grows into proper health checks."""
    return {"status": "ok"}
