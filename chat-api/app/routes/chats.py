from fastapi import APIRouter

from app.models.chat import BaseChat

router = APIRouter(prefix="/chats")


@router.post("/", response_model=BaseChat)
def new_chat():
    pass



@router.post("/{chat_id}/message")
def new_message(chat_id: str, message: str):
    pass
