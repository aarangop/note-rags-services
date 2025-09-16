from fastapi import APIRouter, Depends, HTTPException, Query
from note_rags_db import get_async_db_session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import FileChangeEvent
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
from app.utils.file_processor import (
    FileProcessorRegistry,
    MetadataProcessingError,
)
from app.utils.text_splitter import split_text

router = APIRouter(prefix="/file_events")


@router.post("/", response_model=FileProcessingResponse)
async def process_file_change(
    event: FileChangeEvent, db: AsyncSession = Depends(get_async_db_session)
):
    """
    Process any file change event.

    The processor is selected based on file extension, not API endpoint.
    This keeps the API simple while allowing specialized processing.
    """
    try:
        # Get appropriate processor based on file extension
        processor = FileProcessorRegistry.get_processor(event.file_path)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"File type not supported: {event.file_path}"
        ) from e

    try:
        # All processors work with bytes - let them handle the interpretation
        text, extracted_metadata = processor.parse_content(event.file_content)

        # Merge provided metadata with extracted metadata
        final_metadata = event.metadata or {}
        if extracted_metadata:
            final_metadata.update(extracted_metadata)

        # Check if document exists and has changed
        document = await get_document_by_file_path(db=db, file_path=event.file_path)
        if document and not check_document_changed(db_document=document, new_content=text):
            return FileProcessingResponse(
                document_id=document.id, message="File unchanged", chunks_processed=0
            )

        # Process the content
        chunks = split_text(text)
        embeddings = await get_embeddings(chunks)

        # Store in database
        document_id = await upsert_document(
            db=db, content=text, file_path=event.file_path, metadata=final_metadata
        )

        chunk_objects = create_document_chunks(
            embeddings=embeddings, text=chunks, document_id=document_id
        )

        chunk_ids = await upsert_document_chunks(
            db=db, document_id=document_id, chunks=chunk_objects
        )

        await db.commit()

        return FileProcessingResponse(
            document_id=document_id,
            message=f"File {event.file_path} processed successfully",
            chunks_processed=len(chunk_ids),
        )

    except MetadataProcessingError as e:
        await db.rollback()
        raise HTTPException(
            status_code=422, detail=f"Failed to parse metadata for file {event.file_path}: {str(e)}"
        ) from e
    except Exception as e:
        await db.rollback()
        raise e


@router.delete("/", response_model=FileProcessingResponse)
async def delete_file(
    file_path: str = Query(..., description="Path to the file to delete"),
    db: AsyncSession = Depends(get_async_db_session),
):
    """Delete a file and its associated document chunks."""
    try:
        deleted = await delete_document(db, file_path)
        await db.commit()

        if deleted:
            return FileProcessingResponse(
                message=f"Document '{file_path}' and associated chunks deleted"
            )
        else:
            return FileProcessingResponse(message=f"No document found for '{file_path}'")
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Error deleting file {file_path}: {str(e)}"
        ) from e
