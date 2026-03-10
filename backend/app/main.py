"""
main.py
FastAPI application entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    settings = get_settings()

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()