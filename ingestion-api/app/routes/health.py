import enum
import os
from typing import List

from fastapi import APIRouter, Depends
from langchain.chat_models import init_chat_model
from openai import AuthenticationError
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.db import get_db
from app.services.embeddings import get_embeddings

router = APIRouter(prefix="/health")

llm = init_chat_model(model="chat-gpt-3.5-turbo", model_provider="openai")


class APIHealthState(enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class APIStatus(BaseModel):
    health_state: APIHealthState = Field(default=APIHealthState.UNHEALTHY)
    db_connection: str = Field(default="disconnected")
    embeddings_model: str = Field(default="unavailable")
    errors: List[str] = Field(default=[])
    debug_info: List[str] = Field(default=[])


@router.get("/")
async def check_health(db: AsyncSession = Depends(get_db)):
    status = APIStatus(
        health_state=APIHealthState.UNHEALTHY,
    )

    # Add debug information
    env_openai_key = os.environ.get("OPENAI_API_KEY", "NOT_SET")
    config_key = config.openai_api_key.get_secret_value()

    status.debug_info.append(
        f"ENV OPENAI_API_KEY: {'SET' if env_openai_key != 'NOT_SET' else 'NOT_SET'}"
    )
    status.debug_info.append(
        f"ENV key starts with: {env_openai_key[:15] if env_openai_key != 'NOT_SET' else 'N/A'}"
    )
    status.debug_info.append(f"Config key length: {len(config_key)}")
    status.debug_info.append(f"Config key starts with: {config_key[:15]}")

    try:
        await db.execute(text("SELECT 1"))
        status.db_connection = "connected"
        await get_embeddings(["OK?"])
        status.embeddings_model = "available"
        status.health_state = APIHealthState.HEALTHY
        return status
    except ConnectionRefusedError as e:
        status.errors.append(f"Database connection refused: {e}")
    except AuthenticationError as e:
        status.errors.append(f"OpenAI authentication error: {e.message}")
    except Exception as e:
        status.errors.append(str(e))

    return status
