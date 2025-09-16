from fastapi import APIRouter, Depends
from note_rags_db import get_async_db_session
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Config, get_config
from app.models.query import ContextQuery, Query
from app.services.context import similarity_search
from app.services.embeddings import get_embeddings

router = APIRouter(prefix="/contexts")


class ContextResponse(BaseModel):
    query: Query
    query_embedding: list[float]
    sources: list[str]


@router.get("/")
async def get_context(
    query: ContextQuery,
    db: AsyncSession = Depends(get_async_db_session),
    config: Config = Depends(get_config),
):
    embedding = await get_embeddings(query.question, config)
    chunks = await similarity_search(db=db, query_embedding=embedding, limit=query.limit)
    sources = [row.content for row in chunks]
    return ContextResponse(query=query, query_embedding=embedding, sources=sources)
