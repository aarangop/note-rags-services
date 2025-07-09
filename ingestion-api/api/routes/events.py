from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models.events import FileChangeEvent
from api.services.document_service import (
    create_document_chunks,
    upsert_document,
    upsert_document_chunks,
)
from api.services.embeddings import get_embeddings
from api.utils.file_processor import FileProcessorRegistry
from api.utils.text_splitter import split_text

router = APIRouter(prefix="/file_events")


@router.post("/")
async def process_file_change(
    event: FileChangeEvent, db: AsyncSession = Depends(get_db)
):
    """
    Process a file change event by extracting text, creating embeddings and storing document chunks.

    This function handles file changes by:
    1. Identifying the appropriate processor for the file type
    2. Extracting text and metadata from the file content
    3. Splitting the text into manageable chunks
    4. Generating embeddings for each text chunk
    5. Storing or updating the document in the database
    6. Creating document chunks with embeddings
    7. Storing the document chunks in the database

    Args:
        event (FileChangeEvent): Event containing file path and content information
        db (AsyncSession, optional): Database session. Defaults to Depends(get_db).

    Returns:
        dict: A dictionary containing a success message and the document ID

    Raises:
        HTTPException: If the file type is not supported (400 error)
    """
    try:
        processor = FileProcessorRegistry.get_processor(event.file_path)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"File {event.file_path} not supported"
        )

    text, metadata = processor.extract_text(event.file_content)

    chunks = split_text(text)

    embeddings = await get_embeddings(chunks)

    # First create or update document.
    document_id = await upsert_document(
        db=db, content=text, file_path=event.file_path, metadata=metadata
    )

    chunks = create_document_chunks(
        embeddings=embeddings, text=chunks, document_id=document_id
    )

    chunk_ids = await upsert_document_chunks(
        db=db, document_id=document_id, chunks=chunks
    )

    return {
        "message": f"File {event.file_path} processed. {len(chunk_ids)} chunks upserted",
        "document_id": document_id,
    }
