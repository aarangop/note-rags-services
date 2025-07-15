from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.events import EventType, FileChangeEvent, FileDeletedEvent
from app.models.responses import FileProcessingResponse
from app.services.document_service import (
    check_document_changed,
    create_document_chunks,
    delete_document,
    get_document_by_file_path,
    upsert_document,
    upsert_document_chunks,
)
from app.services.embeddings import get_embeddings
from app.utils.file_processor import FileProcessorRegistry
from app.utils.text_splitter import split_text

router = APIRouter(prefix="/file_events")


@router.post("/", response_model=FileProcessingResponse)
async def process_file_change(event: FileChangeEvent, db: AsyncSession = Depends(get_db)):
    """
    Process a file change event by extracting text, creating embeddings and storing document chunks.

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
        ) from Exception

    try:
        text, metadata = processor.extract_text(event.file_content)

        document = await get_document_by_file_path(db=db, file_path=event.file_path)

        # Check if document changed
        if document and not check_document_changed(db_document=document, new_content=text):
            return FileProcessingResponse(
                document_id=document.id, message="File unchanged", chunks_processed=0
            )

        chunks = split_text(text)

        embeddings = await get_embeddings(chunks)

        # First create or update document.
        document_id = await upsert_document(
            db=db, content=text, file_path=event.file_path, metadata=metadata
        )

        chunks = create_document_chunks(embeddings=embeddings, text=chunks, document_id=document_id)

        chunk_ids = await upsert_document_chunks(db=db, document_id=document_id, chunks=chunks)

        await db.commit()

        return FileProcessingResponse(
            document_id=document_id,
            message=f"File {event.file_path} processed. {len(chunk_ids)} chunks upserted",
            chunks_processed=len(chunk_ids),
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.delete("/", response_model=FileProcessingResponse)
async def delete_file(
   file_path: str = Query(..., description="Path to the file to delete from the database"), db: AsyncSession = Depends(get_db)
    ):
    # Try to find document
    if await delete_document(db, file_path):
        await db.commit()
        return FileProcessingResponse(
            message=f"Document '{file_path}' and its associated chunks deleted",
        )
    else:
        return FileProcessingResponse(
            message="No document found, nothing deleted"
        )