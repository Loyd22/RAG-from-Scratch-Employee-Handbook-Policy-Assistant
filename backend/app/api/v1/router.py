"""
api/v1/router.py
API v1 router that includes all endpoint routers.
"""

from fastapi import APIRouter
from .endpoints import health, ask  # add ask

router = APIRouter()
router.include_router(health.router)
router.include_router(ask.router)   # add this