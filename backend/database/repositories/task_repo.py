"""
FRIDAY OS — Task & AgentLog Repository.

Async CRUD operations for :class:`~backend.database.models.Task` and
:class:`~backend.database.models.AgentLog` models.

Usage::

    async for session in get_async_session():
        repo = TaskRepository(session)
        task = await repo.create(title="Analyse code")
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import AgentLog, Task
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _utcnow() -> datetime:
    """Return the current UTC datetime.

    Returns:
        A timezone-aware UTC :class:`datetime`.
    """
    return datetime.now(UTC)


class TaskRepository:
    """Async repository for Task and AgentLog CRUD operations.

    All methods operate within the provided session and do **not** commit
    or close it — that responsibility belongs to the caller or the
    session lifecycle manager.

    Args:
        session: An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        title: str,
        description: str | None = None,
        conversation_id: str | None = None,
        parent_task_id: str | None = None,
        priority: str = "normal",
    ) -> Task:
        """Create a new task.

        Args:
            title: Short description of the task.
            description: Longer description or instructions.
            conversation_id: Optional FK to the originating conversation.
            parent_task_id: Optional FK for sub-task hierarchy.
            priority: Priority level (low | normal | high | critical).

        Returns:
            The newly created :class:`Task` instance.

        Raises:
            DatabaseError: If the insert fails.
        """
        try:
            task = Task(
                title=title,
                description=description,
                conversation_id=conversation_id,
                parent_task_id=parent_task_id,
                priority=priority,
            )
            self._session.add(task)
            await self._session.flush()
            await self._session.refresh(task)
            logger.info("task_created", task_id=task.id, title=title)
            return task
        except Exception as exc:
            logger.error("task_create_failed", error=str(exc))
            raise DatabaseError(
                message=f"Failed to create task: {exc}",
                error_code="DB_TASK_CREATE",
                details={"title": title, "error": str(exc)},
            ) from exc

    async def get_by_id(self, task_id: str) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: The task's UUID.

        Returns:
            The :class:`Task` instance, or ``None`` if not found.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Task)
                .options(
                    selectinload(Task.subtasks),
                    selectinload(Task.agent_logs),
                )
                .where(Task.id == task_id)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(
                "task_get_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get task: {exc}",
                error_code="DB_TASK_GET",
                details={"task_id": task_id, "error": str(exc)},
            ) from exc

    async def list_by_status(
        self,
        status: str,
        limit: int = 50,
    ) -> list[Task]:
        """List tasks filtered by status.

        Args:
            status: The status to filter on (e.g. ``pending``, ``running``).
            limit: Maximum number of results (default 50).

        Returns:
            A list of :class:`Task` instances ordered by ``created_at``
            descending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Task)
                .where(Task.status == status)
                .order_by(Task.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "task_list_by_status_failed",
                status=status,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to list tasks by status: {exc}",
                error_code="DB_TASK_LIST_STATUS",
                details={"status": status, "error": str(exc)},
            ) from exc

    async def list_by_conversation(
        self,
        conversation_id: str,
    ) -> list[Task]:
        """List all tasks belonging to a conversation.

        Args:
            conversation_id: The parent conversation's UUID.

        Returns:
            A list of :class:`Task` instances ordered by ``created_at``
            ascending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Task)
                .where(Task.conversation_id == conversation_id)
                .order_by(Task.created_at.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "task_list_by_conversation_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to list tasks by conversation: {exc}",
                error_code="DB_TASK_LIST_CONVERSATION",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc

    async def update_status(
        self,
        task_id: str,
        status: str,
    ) -> Task | None:
        """Update a task's status with automatic timestamp management.

        When transitioning to ``running``, sets ``started_at``.
        When transitioning to ``completed`` or ``failed``, sets
        ``completed_at``.

        Args:
            task_id: The task's UUID.
            status: The new status value.

        Returns:
            The updated :class:`Task`, or ``None`` if not found.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = await self._session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                return None

            task.status = status
            now = _utcnow()

            if status == "running" and task.started_at is None:
                task.started_at = now

            if status in ("completed", "failed", "cancelled"):
                task.completed_at = now

            await self._session.flush()
            await self._session.refresh(task)
            logger.info(
                "task_status_updated",
                task_id=task_id,
                status=status,
            )
            return task
        except Exception as exc:
            logger.error(
                "task_status_update_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to update task status: {exc}",
                error_code="DB_TASK_STATUS_UPDATE",
                details={"task_id": task_id, "status": status, "error": str(exc)},
            ) from exc

    async def assign_agent(
        self,
        task_id: str,
        agent_name: str,
    ) -> Task | None:
        """Assign an agent to a task.

        Args:
            task_id: The task's UUID.
            agent_name: Name of the agent to assign.

        Returns:
            The updated :class:`Task`, or ``None`` if not found.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = await self._session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                return None

            task.assigned_agent = agent_name
            await self._session.flush()
            await self._session.refresh(task)
            logger.info(
                "task_agent_assigned",
                task_id=task_id,
                agent_name=agent_name,
            )
            return task
        except Exception as exc:
            logger.error(
                "task_assign_agent_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to assign agent to task: {exc}",
                error_code="DB_TASK_ASSIGN_AGENT",
                details={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "error": str(exc),
                },
            ) from exc

    async def increment_retry(self, task_id: str) -> Task | None:
        """Increment a task's retry counter.

        Args:
            task_id: The task's UUID.

        Returns:
            The updated :class:`Task`, or ``None`` if not found.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Task).where(Task.id == task_id)
            result = await self._session.execute(stmt)
            task = result.scalar_one_or_none()

            if task is None:
                return None

            task.retry_count += 1
            await self._session.flush()
            await self._session.refresh(task)
            logger.info(
                "task_retry_incremented",
                task_id=task_id,
                retry_count=task.retry_count,
            )
            return task
        except Exception as exc:
            logger.error(
                "task_retry_increment_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to increment task retry: {exc}",
                error_code="DB_TASK_RETRY_INCREMENT",
                details={"task_id": task_id, "error": str(exc)},
            ) from exc

    async def get_pending_tasks(self, limit: int = 20) -> list[Task]:
        """Retrieve pending tasks ordered by priority and creation time.

        Priority ordering: ``critical`` > ``high`` > ``normal`` > ``low``.

        Args:
            limit: Maximum number of results (default 20).

        Returns:
            A list of pending :class:`Task` instances.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            from sqlalchemy import case

            priority_order = case(
                {"critical": 0, "high": 1, "normal": 2, "low": 3},
                value=Task.priority,
                else_=4,
            )
            stmt = (
                select(Task)
                .where(Task.status == "pending")
                .order_by(priority_order, Task.created_at.asc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("pending_tasks_get_failed", error=str(exc))
            raise DatabaseError(
                message=f"Failed to get pending tasks: {exc}",
                error_code="DB_PENDING_TASKS_GET",
                details={"error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # AgentLog CRUD
    # ------------------------------------------------------------------

    async def add_agent_log(
        self,
        task_id: str,
        agent_name: str,
        action: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        status: str = "completed",
        duration: float | None = None,
    ) -> AgentLog:
        """Record an agent action log entry.

        Args:
            task_id: The parent task's UUID.
            agent_name: Name of the acting agent.
            action: Description of the action performed.
            input_data: Optional input data dictionary (serialised as JSON).
            output_data: Optional output data dictionary (serialised as JSON).
            status: Action status (default ``completed``).
            duration: Execution duration in seconds.

        Returns:
            The newly created :class:`AgentLog` instance.

        Raises:
            DatabaseError: If the insert fails.
        """
        try:
            input_json: str | None = None
            if input_data is not None:
                input_json = orjson.dumps(input_data).decode("utf-8")

            output_json: str | None = None
            if output_data is not None:
                output_json = orjson.dumps(output_data).decode("utf-8")

            agent_log = AgentLog(
                task_id=task_id,
                agent_name=agent_name,
                action=action,
                input_json=input_json,
                output_json=output_json,
                status=status,
                duration_seconds=duration,
            )
            self._session.add(agent_log)
            await self._session.flush()
            await self._session.refresh(agent_log)
            logger.info(
                "agent_log_added",
                log_id=agent_log.id,
                task_id=task_id,
                agent_name=agent_name,
                action=action,
            )
            return agent_log
        except Exception as exc:
            logger.error(
                "agent_log_add_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to add agent log: {exc}",
                error_code="DB_AGENT_LOG_ADD",
                details={
                    "task_id": task_id,
                    "agent_name": agent_name,
                    "error": str(exc),
                },
            ) from exc

    async def get_agent_logs(self, task_id: str) -> list[AgentLog]:
        """Retrieve all agent log entries for a task.

        Args:
            task_id: The parent task's UUID.

        Returns:
            A list of :class:`AgentLog` instances ordered by ``created_at``
            ascending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(AgentLog)
                .where(AgentLog.task_id == task_id)
                .order_by(AgentLog.created_at.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "agent_logs_get_failed",
                task_id=task_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get agent logs: {exc}",
                error_code="DB_AGENT_LOGS_GET",
                details={"task_id": task_id, "error": str(exc)},
            ) from exc
