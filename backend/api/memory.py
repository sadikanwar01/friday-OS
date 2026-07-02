from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.api.deps import get_memory_manager
from backend.memory.manager import MemoryManager
from backend.utils.logger import get_logger

router = APIRouter(prefix="/api", tags=["memory"])
logger = get_logger(__name__)


@router.get("/memory", response_model=list[dict[str, Any]])
async def get_memories(
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> list[dict[str, Any]]:
    """Retrieve long-term memory points."""
    # We query the SQLite DB directly through the session since memory_manager
    # doesn't have a direct "list all" method yet.
    try:
        result = await memory_manager.sql_repo._session.execute(
            text("SELECT * FROM memories ORDER BY created_at DESC LIMIT 50")
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error("memory_fetch_failed", error=str(e))
        return []


@router.get("/history", response_model=list[dict[str, Any]])
async def get_history(
    memory_manager: MemoryManager = Depends(get_memory_manager),
) -> list[dict[str, Any]]:
    """Retrieve recent conversation history."""
    try:
        result = await memory_manager.sql_repo._session.execute(
            text("SELECT * FROM messages ORDER BY created_at DESC LIMIT 100")
        )
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error("history_fetch_failed", error=str(e))
        return []
