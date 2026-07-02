from fastapi import APIRouter

from backend.api.automation import router as automation_router
from backend.api.browser import router as browser_router
from backend.api.chat import router as chat_router
from backend.api.memory import router as memory_router
from backend.api.system import router as system_router
from backend.api.voice import router as voice_router

api_router = APIRouter()

api_router.include_router(chat_router)
api_router.include_router(memory_router)
api_router.include_router(automation_router)
api_router.include_router(browser_router)
api_router.include_router(voice_router)
api_router.include_router(system_router)
