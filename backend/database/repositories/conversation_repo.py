"""
FRIDAY OS — Conversation & Message Repository.

Async CRUD operations for :class:`~backend.database.models.Conversation`
and :class:`~backend.database.models.Message` models.

Usage::

    async for session in get_async_session():
        repo = ConversationRepository(session)
        conv = await repo.create(user_id="...", title="New chat")
"""

from __future__ import annotations

from typing import Any

import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import Conversation, Message
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """Async repository for Conversation and Message CRUD operations.

    All methods operate within the provided session and do **not** commit
    or close it — that responsibility belongs to the caller or the
    session lifecycle manager.

    Args:
        session: An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Conversation CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: str,
        title: str | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id: The ID of the owning user.
            title: Optional conversation title.

        Returns:
            The newly created :class:`Conversation` instance.

        Raises:
            DatabaseError: If the insert fails.
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                title=title,
            )
            self._session.add(conversation)
            await self._session.flush()
            await self._session.refresh(conversation)
            logger.info(
                "conversation_created",
                conversation_id=conversation.id,
                user_id=user_id,
            )
            return conversation
        except Exception as exc:
            logger.error("conversation_create_failed", error=str(exc))
            raise DatabaseError(
                message=f"Failed to create conversation: {exc}",
                error_code="DB_CONVERSATION_CREATE",
                details={"user_id": user_id, "error": str(exc)},
            ) from exc

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        """Retrieve a conversation by its ID.

        Args:
            conversation_id: The conversation's UUID.

        Returns:
            The :class:`Conversation` instance, or ``None`` if not found.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Conversation)
                .options(
                    selectinload(Conversation.messages),
                    selectinload(Conversation.tasks),
                )
                .where(Conversation.id == conversation_id)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(
                "conversation_get_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get conversation: {exc}",
                error_code="DB_CONVERSATION_GET",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List conversations for a user, ordered by most recently updated.

        Args:
            user_id: The owning user's ID.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            A list of :class:`Conversation` instances.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "conversation_list_failed",
                user_id=user_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to list conversations: {exc}",
                error_code="DB_CONVERSATION_LIST",
                details={"user_id": user_id, "error": str(exc)},
            ) from exc

    async def update(
        self,
        conversation_id: str,
        **kwargs: Any,
    ) -> Conversation | None:
        """Update a conversation's fields.

        Accepted keyword arguments correspond to :class:`Conversation`
        column names (e.g. ``title``, ``summary``, ``status``).

        Args:
            conversation_id: The conversation's UUID.
            **kwargs: Fields to update.

        Returns:
            The updated :class:`Conversation`, or ``None`` if not found.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
            )
            result = await self._session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation is None:
                return None

            for attr, value in kwargs.items():
                if hasattr(conversation, attr):
                    setattr(conversation, attr, value)

            await self._session.flush()
            await self._session.refresh(conversation)
            logger.info(
                "conversation_updated",
                conversation_id=conversation_id,
                fields=list(kwargs.keys()),
            )
            return conversation
        except Exception as exc:
            logger.error(
                "conversation_update_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to update conversation: {exc}",
                error_code="DB_CONVERSATION_UPDATE",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation and all its related messages/tasks.

        Args:
            conversation_id: The conversation's UUID.

        Returns:
            ``True`` if the conversation was found and deleted, ``False``
            otherwise.

        Raises:
            DatabaseError: If the deletion fails.
        """
        try:
            stmt = select(Conversation).where(
                Conversation.id == conversation_id,
            )
            result = await self._session.execute(stmt)
            conversation = result.scalar_one_or_none()

            if conversation is None:
                return False

            await self._session.delete(conversation)
            await self._session.flush()
            logger.info(
                "conversation_deleted",
                conversation_id=conversation_id,
            )
            return True
        except Exception as exc:
            logger.error(
                "conversation_delete_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to delete conversation: {exc}",
                error_code="DB_CONVERSATION_DELETE",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Message CRUD
    # ------------------------------------------------------------------

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Add a new message to a conversation.

        Args:
            conversation_id: The parent conversation's UUID.
            role: Message role (``user``, ``assistant``, ``system``).
            content: The message text.
            message_type: Type of message (default ``text``).
            metadata: Optional metadata dictionary (serialised as JSON).

        Returns:
            The newly created :class:`Message` instance.

        Raises:
            DatabaseError: If the insert fails.
        """
        try:
            metadata_json: str | None = None
            if metadata is not None:
                metadata_json = orjson.dumps(metadata).decode("utf-8")

            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata_json=metadata_json,
            )
            self._session.add(message)
            await self._session.flush()
            await self._session.refresh(message)
            logger.info(
                "message_added",
                message_id=message.id,
                conversation_id=conversation_id,
                role=role,
            )
            return message
        except Exception as exc:
            logger.error(
                "message_add_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to add message: {exc}",
                error_code="DB_MESSAGE_ADD",
                details={
                    "conversation_id": conversation_id,
                    "role": role,
                    "error": str(exc),
                },
            ) from exc

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        """Retrieve messages for a conversation, oldest first.

        Args:
            conversation_id: The parent conversation's UUID.
            limit: Maximum number of results (default 100).
            offset: Number of results to skip (default 0).

        Returns:
            A list of :class:`Message` instances ordered by ``created_at``
            ascending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "messages_get_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get messages: {exc}",
                error_code="DB_MESSAGES_GET",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc

    async def get_recent_messages(
        self,
        conversation_id: str,
        count: int = 10,
    ) -> list[Message]:
        """Retrieve the most recent messages for a conversation.

        The messages are returned in chronological order (oldest first)
        even though only the *last* ``count`` messages are selected.

        Args:
            conversation_id: The parent conversation's UUID.
            count: Number of recent messages to retrieve (default 10).

        Returns:
            A list of :class:`Message` instances in chronological order.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            # Sub-query: get the most recent N messages (newest first).
            subq = (
                select(Message.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(count)
                .subquery()
            )
            # Main query: re-select those rows in chronological order.
            stmt = (
                select(Message)
                .where(Message.id.in_(select(subq.c.id)))
                .order_by(Message.created_at.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "recent_messages_get_failed",
                conversation_id=conversation_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get recent messages: {exc}",
                error_code="DB_RECENT_MESSAGES_GET",
                details={"conversation_id": conversation_id, "error": str(exc)},
            ) from exc
