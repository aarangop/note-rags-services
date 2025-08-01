import uuid

from fastapi import Depends

from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate
from app.repositories.conversation_repository import ConversationRepository, get_chat_repository


class ConversationNotFoundError(Exception):
    pass


class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    async def create(self, conversation: ConversationCreate) -> Conversation:
        return await self.repository.create(conversation)

    async def update(self, conversation: ConversationUpdate) -> Conversation:
        updated_conversation = await self.repository.update(
            conversation_id=conversation.id, conversation_update=conversation
        )
        if updated_conversation:
            return updated_conversation
        raise ConversationNotFoundError(f"Conversation {conversation.id} was not found")

    async def delete(self, conversation_id: uuid.UUID) -> bool:
        return await self.repository.delete(conversation_id)


def get_conversation_service(repository: ConversationRepository = Depends(get_chat_repository)):
    return ConversationService(repository=repository)
