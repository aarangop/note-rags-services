from note_rags_db.schemas import DocumentChunk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def similarity_search(db: AsyncSession, query_embedding: list[float], limit=4):
    statement = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await db.execute(statement)
    return result.scalars().all()
