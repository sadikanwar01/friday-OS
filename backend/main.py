"""
FRIDAY OS — Application Entry Point.

FastAPI application exposing the core FRIDAY OS engines.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import api_router
from backend.api.middleware import setup_middlewares
from backend.automation.coordinator import ExecutionCoordinator
from backend.automation.engine import AutomationEngine
from backend.automation.registry import ToolRegistry
from backend.automation.safety import PermissionManager, SafetyLayer
from backend.automation.tools.browser import BrowserTool
from backend.automation.tools.clipboard import ClipboardTool
from backend.automation.tools.fs import FileSystemTool
from backend.automation.tools.gui import KeyboardTool, MouseTool, ScreenshotTool, WindowTool
from backend.automation.tools.terminal import TerminalTool
from backend.config import get_settings
from backend.database import async_session_factory
from backend.database.engine import close_database, init_database
from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine
from backend.utils.logger import get_logger
from backend.voice.pipeline import VoiceSessionManager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: initialise services on startup, clean up on shutdown."""
    settings = get_settings()
    settings.voice_mode = "push_to_talk"
    logger.info(
        "friday_starting",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )

    await init_database()
    logger.info("database_ready")

    # Initialize core singletons
    session = async_session_factory()
    memory_manager = MemoryManager(session=session)
    planner = PlanningEngine(memory_manager)

    pm = PermissionManager()
    # For API we allow execution based on normal safety rules, no REPL block
    safety_layer = SafetyLayer(permission_manager=pm, default_mode="auto")

    registry = ToolRegistry()
    registry.register(TerminalTool())
    registry.register(FileSystemTool())
    registry.register(ClipboardTool())
    registry.register(MouseTool())
    registry.register(KeyboardTool())
    registry.register(WindowTool())
    registry.register(ScreenshotTool())
    registry.register(BrowserTool())

    automation_engine = AutomationEngine(registry=registry, safety_layer=safety_layer)
    execution_coordinator = ExecutionCoordinator(automation_engine=automation_engine)

    voice = VoiceSessionManager(
        memory_manager=memory_manager,
        planning_engine=planner,
        execution_coordinator=execution_coordinator
    )
    await voice.initialize()

    # Attach to app.state for dependency injection
    app.state.memory_manager = memory_manager
    app.state.planner = planner
    app.state.automation_engine = automation_engine
    app.state.coordinator = execution_coordinator
    app.state.voice = voice

    logger.info("friday_engines_ready")

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

    setup_middlewares(app)
    app.include_router(api_router)

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
