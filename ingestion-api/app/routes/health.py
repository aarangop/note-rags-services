import enum

from fastapi import APIRouter, Depends
from note_rags_db import get_async_db_session
from openai import AuthenticationError
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import get_embeddings

router = APIRouter(prefix="/health")


class APIHealthState(enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class APIStatus(BaseModel):
    health_state: APIHealthState = Field(default=APIHealthState.UNHEALTHY)
    db_connection: str = Field(default="disconnected")
    embeddings_model: str = Field(default="unavailable")
    errors: list[str] = Field(default=[])


@router.get("/")
async def check_health(db: AsyncSession = Depends(get_async_db_session)):
    status = APIStatus(
        health_state=APIHealthState.UNHEALTHY,
    )

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
