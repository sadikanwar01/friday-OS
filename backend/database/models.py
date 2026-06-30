"""
FRIDAY OS — SQLAlchemy ORM Models.

Defines the complete database schema for FRIDAY OS using SQLAlchemy 2.0+
declarative mapping.  All models inherit from :class:`Base` and use
``mapped_column`` with full type annotations.

Tables:
    - ``users`` — registered users with preferences and security mode.
    - ``conversations`` — chat conversations belonging to users.
    - ``messages`` — individual messages within conversations.
    - ``tasks`` — work items with status tracking and agent assignment.
    - ``agent_logs`` — audit log for every agent action within a task.
    - ``memories`` — long-term user memory with importance scoring.
    - ``security_audit`` — security decision audit trail.
    - ``settings`` — key/value application settings.

Usage::

    from backend.database.models import Base, User, Conversation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ---------------------------------------------------------------------------
# UUID generator
# ---------------------------------------------------------------------------

def _generate_uuid() -> str:
    """Generate a new UUID4 string for use as a primary key default.

    Returns:
        A string representation of a new UUID4.
    """
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Shared declarative base for all FRIDAY OS models."""

    pass


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    """A registered FRIDAY OS user.

    Attributes:
        id: Unique user identifier (UUID4).
        name: Display name of the user.
        preferences_json: JSON-encoded user preferences.
        security_mode: Execution safety mode (safe | confirm | auto).
        created_at: Timestamp when the user was created.
        updated_at: Timestamp when the user was last modified.
        conversations: Related conversations.
        memories: Related long-term memories.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    preferences_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    security_mode: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="confirm",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # -- Relationships --------------------------------------------------------
    conversations: Mapped[list[Conversation]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    memories: Mapped[list[Memory]] = relationship(
        "Memory",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} name={self.name!r}>"


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

class Conversation(Base):
    """A conversation session between a user and FRIDAY.

    Attributes:
        id: Unique conversation identifier (UUID4).
        user_id: Foreign key to the owning user.
        title: Optional conversation title.
        summary: Optional conversation summary.
        status: Current status (active | archived | deleted).
        created_at: Timestamp when the conversation was created.
        updated_at: Timestamp when the conversation was last modified.
        messages: Related messages.
        tasks: Related tasks.
        user: The owning user.
    """

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # -- Relationships --------------------------------------------------------
    user: Mapped[User] = relationship(
        "User",
        back_populates="conversations",
    )
    messages: Mapped[list[Message]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )
    tasks: Mapped[list[Task]] = relationship(
        "Task",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation id={self.id!r} status={self.status!r}>"


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

class Message(Base):
    """A single message within a conversation.

    Attributes:
        id: Unique message identifier (UUID4).
        conversation_id: Foreign key to the parent conversation.
        role: Message author role (user | assistant | system).
        content: The message text content.
        message_type: Type of message (text | image | tool_call | etc.).
        metadata_json: Optional JSON-encoded metadata.
        created_at: Timestamp when the message was created.
        conversation: The parent conversation.
    """

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    # -- Relationships --------------------------------------------------------
    conversation: Mapped[Conversation] = relationship(
        "Conversation",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<Message id={self.id!r} role={self.role!r}>"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task(Base):
    """A work item tracked by the task pipeline.

    Tasks can be nested via ``parent_task_id`` and assigned to specific
    agents.  Status transitions drive ``started_at`` and ``completed_at``
    timestamps.

    Attributes:
        id: Unique task identifier (UUID4).
        conversation_id: Optional FK to the originating conversation.
        parent_task_id: Optional FK for sub-task hierarchy.
        title: Short description of the task.
        description: Longer description or instructions.
        status: Current status (pending | running | completed | failed | cancelled).
        assigned_agent: Name of the agent handling this task.
        priority: Priority level (low | normal | high | critical).
        result_json: JSON-encoded result data.
        retry_count: Number of retry attempts made.
        created_at: Timestamp when the task was created.
        started_at: Timestamp when execution began.
        completed_at: Timestamp when execution finished.
        conversation: The originating conversation (if any).
        parent_task: The parent task (if any).
        subtasks: Child tasks.
        agent_logs: Audit log entries for this task.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("conversations.id"),
        nullable=True,
    )
    parent_task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    assigned_agent: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
    )
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # -- Relationships --------------------------------------------------------
    conversation: Mapped[Optional[Conversation]] = relationship(
        "Conversation",
        back_populates="tasks",
    )
    parent_task: Mapped[Optional[Task]] = relationship(
        "Task",
        remote_side="Task.id",
        back_populates="subtasks",
    )
    subtasks: Mapped[list[Task]] = relationship(
        "Task",
        back_populates="parent_task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    agent_logs: Mapped[list[AgentLog]] = relationship(
        "AgentLog",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id!r} status={self.status!r}>"


# ---------------------------------------------------------------------------
# AgentLog
# ---------------------------------------------------------------------------

class AgentLog(Base):
    """Audit log entry for a single agent action within a task.

    Attributes:
        id: Unique log entry identifier (UUID4).
        task_id: Foreign key to the parent task.
        agent_name: Name of the agent that performed the action.
        action: Description of the action taken.
        input_json: JSON-encoded input data.
        output_json: JSON-encoded output data.
        status: Outcome status (completed | failed | skipped).
        duration_seconds: Execution duration in seconds.
        created_at: Timestamp when the log entry was created.
        task: The parent task.
    """

    __tablename__ = "agent_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    task_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    input_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    # -- Relationships --------------------------------------------------------
    task: Mapped[Task] = relationship(
        "Task",
        back_populates="agent_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentLog id={self.id!r} agent={self.agent_name!r} "
            f"action={self.action!r}>"
        )


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class Memory(Base):
    """Long-term memory entry for a user.

    Memories are categorised and scored by importance.  Access tracking
    (``access_count``, ``last_accessed``) supports recency-based retrieval.

    Attributes:
        id: Unique memory identifier (UUID4).
        user_id: Foreign key to the owning user.
        category: Memory category (preference | project | routine | etc.).
        key: Lookup key for the memory.
        value: The memory content.
        metadata_json: Optional JSON-encoded metadata.
        importance_score: Importance score between 0.0 and 1.0.
        created_at: Timestamp when the memory was created.
        last_accessed: Timestamp when the memory was last read.
        access_count: Number of times this memory has been accessed.
        user: The owning user.
    """

    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(500), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    last_accessed: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    access_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # -- Relationships --------------------------------------------------------
    user: Mapped[User] = relationship(
        "User",
        back_populates="memories",
    )

    # -- Table-level indexes --------------------------------------------------
    __table_args__ = (
        Index("ix_memories_user_category", "user_id", "category"),
        Index("ix_memories_user_key", "user_id", "key"),
    )

    def __repr__(self) -> str:
        return f"<Memory id={self.id!r} key={self.key!r}>"


# ---------------------------------------------------------------------------
# SecurityAudit
# ---------------------------------------------------------------------------

class SecurityAudit(Base):
    """Audit trail entry for a security decision.

    Attributes:
        id: Unique audit entry identifier (UUID4).
        action_type: Type of action being audited.
        action_detail: Detailed description of the action.
        security_mode: Security mode active at decision time.
        decision: Outcome of the security check (allowed | denied | pending).
        reason: Human-readable reason for the decision.
        created_at: Timestamp when the audit entry was created.
    """

    __tablename__ = "security_audit"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    security_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<SecurityAudit id={self.id!r} action={self.action_type!r} "
            f"decision={self.decision!r}>"
        )


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------

class Setting(Base):
    """A key/value application setting.

    Attributes:
        id: Unique setting identifier (UUID4).
        key: Unique setting key.
        value: Setting value (stored as text).
        category: Setting category for grouping (default: 'general').
        updated_at: Timestamp when the setting was last modified.
    """

    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
    )
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Setting key={self.key!r} category={self.category!r}>"
