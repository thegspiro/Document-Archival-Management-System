"""Health check endpoint — no authentication required."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/health", status_code=200)
async def health_check() -> dict[str, str]:
    """Return a simple health status for load balancers and orchestrators."""
    return {"status": "ok"}
