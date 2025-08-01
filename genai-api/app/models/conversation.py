import uuid
from datetime import datetime
from typing import Any

from note_rags_db.schemas.conversation import MessageRole
from pydantic import BaseModel, ConfigDict, Field


class BaseMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: MessageRole
    conversation_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)


class Message(BaseMessage):
    id: uuid.UUID
    content: str
    message_metadata: dict[str, Any] = Field(default={})


class BaseConversation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime | None = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default_factory=datetime.now)


class ConversationCreate(BaseConversation):
    title: str | None = None
    conversation_metadata: dict[str, Any] | None = None
    messages: list[Message] | None = None


class ConversationUpdate(BaseConversation):
    id: uuid.UUID
    title: str | None = None
    conversation_metadata: dict[str, Any] | None = None


class Conversation(BaseConversation):
    id: uuid.UUID
    title: str
    messages: list[Message] = Field(default=[])
    conversation_metadata: dict[str, Any] = Field(default={})
