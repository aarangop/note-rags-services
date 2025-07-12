from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from note_rags_db.schemas import DocumentChunk, Document

async def upsert_document(
    db: AsyncSession,
    file_path: str,
    content: str,
) -> int:
    """Create or update document, return document ID"""

    document = await get_document_by_file_path(db, file_path)

    if document:
        document.content = content
        # Clear existing chunks
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
        )
    else:
        document = Document(file_path=file_path, content=content)
        db.add(document)
        await db.flush()  # Get ID

    return document.id


async def get_document_by_file_path(
    db: AsyncSession, file_path: str
) -> Document | None:
    """Retrieve a document by its file path

    Args:
        db: Database session
        file_path: Path to the document file

    Returns:
        Document object if found, None otherwise
    """
    result = await db.execute(select(Document).where(Document.file_path == file_path))
    return result.scalar_one_or_none()


def create_document_chunks(
    embeddings: List[List[float]], text: List[str], document_id: int
) -> List[DocumentChunk]:
    """Create document chunks from embeddings and text

    Args:
        embeddings: List of embedding vectors
        text: List of text chunks
        document_id: ID of the parent document

    Returns:
        List of DocumentChunk objects
    """
    if len(embeddings) != len(text):
        raise ValueError("Number of embeddings must match number of text chunks")

    chunks = []
    for i, (embedding, content) in enumerate(zip(embeddings, text)):
        chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            embedding=embedding,
            chunk_index=i,
        )
        chunks.append(chunk)

    return chunks


async def upsert_document_chunks(
    db: AsyncSession, document_id: int, chunks: List[DocumentChunk]
) -> List[int]:
    """Upsert document chunks, returning the ids of the upserted chunks"""
    chunk_ids = []
    for chunk in chunks:
        # Ensure the chunk is associated with the document
        chunk.document_id = document_id
        db.add(chunk)

    await db.flush()  # Flush to get IDs for all chunks

    # Collect all chunk IDs
    chunk_ids = [chunk.id for chunk in chunks]
    return chunk_ids
