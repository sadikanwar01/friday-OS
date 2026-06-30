"""
FRIDAY OS — Application Entry Point.

Minimal FastAPI application for Phase 1 verification.
Provides a health-check endpoint and initialises the database on startup.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from backend.config import get_settings
from backend.database.engine import init_database, close_database
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: initialise services on startup, clean up on shutdown."""
    settings = get_settings()
    logger.info(
        "friday_starting",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    await init_database()
    logger.info("database_ready")

    yield

    await close_database()
    logger.info("friday_shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="FRIDAY OS — AI Operating System",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> dict:
        """System health check endpoint."""
        return {
            "status": "online",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    return app


app = create_app()
