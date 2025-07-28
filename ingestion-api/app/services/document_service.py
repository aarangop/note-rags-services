import hashlib
from pathlib import Path

import structlog
from note_rags_db.schemas import Document, DocumentChunk
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


def calculate_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def check_document_changed(db_document: Document, new_content: str) -> bool:
    new_hash = calculate_content_hash(new_content)
    return new_hash != db_document.content_hash


async def upsert_document(db: AsyncSession, file_path: str, content: str, metadata: dict) -> int:
    """Create or update document, return document ID"""
    document = await get_document_by_file_path(db, file_path)
    if document:
        if not check_document_changed(document, content):
            logger.debug("Document unchaged, skipping", document_id=document.id)
            return document.id
        document.content = content
        document.content_hash = calculate_content_hash(content)
        document.document_metadata = metadata
        # Clear existing chunks
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    else:
        title = Path(file_path).stem
        content_hash = calculate_content_hash(content)
        try:
            document = Document(
                file_path=file_path,
                content=content,
                content_hash=content_hash,
                title=title,
                document_metadata=metadata,
            )
            db.add(document)
            await db.flush()  # Get ID
        except IntegrityError as e:
            raise e

    return document.id


async def delete_document(db: AsyncSession, file_path: str):
    document = await get_document_by_file_path(db, file_path)

    if not document:
        return False

    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))

    await db.execute(delete(Document).where(Document.id == document.id))

    return True


async def get_document_by_file_path(db: AsyncSession, file_path: str) -> Document | None:
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
    embeddings: list[list[float]], text: list[str], document_id: int
) -> list[DocumentChunk]:
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
    for i, (embedding, content) in enumerate(zip(embeddings, text, strict=False)):
        chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            embedding=embedding,
            chunk_index=i,
        )
        chunks.append(chunk)

    return chunks


async def upsert_document_chunks(
    db: AsyncSession, document_id: int, chunks: list[DocumentChunk]
) -> list[int]:
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
