import uuid

from fastapi import Depends
from note_rags_db import get_async_db_session
from note_rags_db.schemas.conversation import Conversation as ConversationSchema
from note_rags_db.schemas.conversation import Message as MessageSchema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, conversation: ConversationCreate) -> Conversation:
        """Create a new conversation in the database."""
        try:
            # Create the database schema object
            db_conversation = ConversationSchema(
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                conversation_metadata=conversation.conversation_metadata or {},
            )

            if conversation.messages:
                # Add messages if any
                for message in conversation.messages:
                    db_message = MessageSchema(
                        role=message.role,
                        content=message.content,
                        conversation_id=db_conversation.id,
                        created_at=message.created_at,
                        message_metadata=message.message_metadata or {},
                    )
                    db_conversation.messages.append(db_message)

            self.db.add(db_conversation)
            await self.db.commit()
            await self.db.refresh(db_conversation)

            return Conversation.model_validate(db_conversation)
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Get a conversation by its ID."""
        statement = (
            select(ConversationSchema)
            .options(selectinload(ConversationSchema.messages))
            .where(ConversationSchema.id == conversation_id)
        )
        result = await self.db.execute(statement)
        db_conversation = result.scalar_one_or_none()

        if db_conversation is None:
            return None

        return Conversation.model_validate(db_conversation)

    async def get(self, limit: int = 100, offset: int = 0) -> list[Conversation]:
        """Get all conversations with pagination."""
        statement = (
            select(ConversationSchema)
            .options(selectinload(ConversationSchema.messages))
            .offset(offset)
            .limit(limit)
            .order_by(ConversationSchema.updated_at.desc())
        )
        result = await self.db.execute(statement)
        db_conversations = result.scalars().all()

        return [
            Conversation.model_validate(db_conversation) for db_conversation in db_conversations
        ]

    async def update(
        self, conversation_id: uuid.UUID, conversation_update: ConversationUpdate
    ) -> Conversation | None:
        """Update an existing conversation."""
        db_conversation = await self.db.get(ConversationSchema, conversation_id)
        if db_conversation is None:
            return None

        # Update conversation fields
        db_conversation.title = conversation_update.title
        if conversation_update.updated_at is not None:
            db_conversation.updated_at = conversation_update.updated_at
        db_conversation.conversation_metadata = conversation_update.conversation_metadata or {}

        await self.db.commit()
        await self.db.refresh(db_conversation)

        return Conversation.model_validate(db_conversation)

    async def delete(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation by its ID."""
        db_conversation = await self.db.get(ConversationSchema, conversation_id)
        if db_conversation is None:
            return False

        await self.db.delete(db_conversation)
        await self.db.commit()
        return True


def get_chat_repository(db: AsyncSession = Depends(get_async_db_session)):
    return ConversationRepository(db)
