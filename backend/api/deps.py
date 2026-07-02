from fastapi import Request

from backend.automation.coordinator import ExecutionCoordinator
from backend.automation.engine import AutomationEngine
from backend.memory.manager import MemoryManager
from backend.planner.engine import PlanningEngine
from backend.voice.pipeline import VoiceSessionManager


def get_memory_manager(request: Request) -> MemoryManager:
    return request.app.state.memory_manager


def get_planner(request: Request) -> PlanningEngine:
    return request.app.state.planner


def get_automation_engine(request: Request) -> AutomationEngine:
    return request.app.state.automation_engine


def get_coordinator(request: Request) -> ExecutionCoordinator:
    return request.app.state.coordinator


def get_voice_manager(request: Request) -> VoiceSessionManager:
    return request.app.state.voice
