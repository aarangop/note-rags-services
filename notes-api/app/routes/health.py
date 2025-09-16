import enum

from fastapi import APIRouter, Depends
from note_rags_db import get_async_db_session
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["health"])


class APIHealthState(enum.Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class APIStatus(BaseModel):
    health_state: APIHealthState = Field(default=APIHealthState.UNHEALTHY)
    db_connection: str = Field(default="disconnected")
    errors: list[str] = Field(default=[])


@router.get("/")
async def check_health(db: AsyncSession = Depends(get_async_db_session)):
    status = APIStatus(
        health_state=APIHealthState.UNHEALTHY,
    )

    try:
        await db.execute(text("SELECT 1"))
        status.db_connection = "connected"
        status.health_state = APIHealthState.HEALTHY
        return status
    except ConnectionRefusedError as e:
        status.errors.append(f"Database connection refused: {e}")
    except Exception as e:
        status.errors.append(str(e))

    return status
