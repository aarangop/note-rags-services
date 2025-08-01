"""
Conversation schema for the GenAI API.
Add this to: db/src/note_rags_db/schemas/conversation.py
"""

import datetime
import uuid
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from note_rags_db.db import Base
from note_rags_db.schemas.document import DocumentChunk


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """Conversation model for storing chat sessions."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(default=func.now(), onupdate=func.now())
    conversation_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default={}
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    context_chunks: Mapped[list["ConversationContext"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}')>"


class Message(Base):
    """Message model for storing individual messages in conversations."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    role: Mapped[MessageRole] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default={})
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class ConversationContext(Base):
    """Many-to-many relationship between conversations and document chunks."""

    __tablename__ = "conversation_context"

    id: Mapped[int] = mapped_column(primary_key=True)  # Keep int for junction table
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id")
    )
    document_chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"))
    relevance_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="context_chunks")
    document_chunk: Mapped["DocumentChunk"] = relationship()

    def __repr__(self) -> str:
        return f"<ConversationContext(conversation_id={self.conversation_id}, chunk_id={self.document_chunk_id}, score={self.relevance_score})>"
