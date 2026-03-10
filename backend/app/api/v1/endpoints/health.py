"""
api/v1/endpoints/health.py
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict:
    """Return a simple health status response."""
    return {"status": "ok"}