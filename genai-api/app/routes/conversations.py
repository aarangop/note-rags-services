import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.models.conversation import Conversation, ConversationCreate, ConversationUpdate
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
    get_conversation_service,
)

router = APIRouter(prefix="/conversations")


@router.post("/", response_model=Conversation)
async def new_conversation(
    conversation: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        return await service.create(conversation)
    except Exception as e:
        raise e


@router.put("/", response_model=Conversation)
async def update_conversation(
    conversation: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    try:
        return await service.update(conversation)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Conversation {conversation.id} not found"
        ) from e
    except Exception as e:
        raise e


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID, service: ConversationService = Depends(get_conversation_service)
):
    try:
        return await service.delete(conversation_id)
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=404, detail=f"Conversation {conversation_id} not found"
        ) from e
    except Exception as e:
        raise e


@router.post("/{conversation_id}/message")
def new_message(conversation_id: str, message: str):
    pass
