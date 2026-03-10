"""
core/config.py
App settings loaded from environment variables.
"""

from pydantic import BaseModel
import os


class Settings(BaseModel):
    """Strongly-typed application settings."""

    app_name: str = os.getenv("APP_NAME", "rag-policy-assistant")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    """Return application settings."""
    return Settings()