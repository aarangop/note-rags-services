from note_rags_db.schemas import DocumentChunk
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def similarity_search(db: AsyncSession, query_embedding: List[float], limit=4):
    statement = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await db.execute(statement)
    return result.scalars().all()