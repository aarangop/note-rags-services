from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.events import BinaryFileChangeEvent, TextFileChangeEvent
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


async def _process_file_content(
    file_path: str, content_bytes: bytes, metadata: dict | None, db: AsyncSession
) -> FileProcessingResponse:
    """
    Common file processing logic for both text and binary endpoints.
    """
    try:
        processor = FileProcessorRegistry.get_processor(file_path)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"File {file_path} not supported"
        ) from Exception

    try:
        text, extracted_metadata = processor.parse_content(content_bytes)

        # Merge provided metadata with extracted metadata
        final_metadata = metadata or {}
        if extracted_metadata:
            final_metadata.update(extracted_metadata)

        document = await get_document_by_file_path(db=db, file_path=file_path)

        # Check if document changed
        if document and not check_document_changed(db_document=document, new_content=text):
            return FileProcessingResponse(
                document_id=document.id, message="File unchanged", chunks_processed=0
            )

        chunks = split_text(text)
        embeddings = await get_embeddings(chunks)

        # First create or update document.
        document_id = await upsert_document(
            db=db, content=text, file_path=file_path, metadata=final_metadata
        )

        chunks = create_document_chunks(embeddings=embeddings, text=chunks, document_id=document_id)
        chunk_ids = await upsert_document_chunks(db=db, document_id=document_id, chunks=chunks)
        await db.commit()

        return FileProcessingResponse(
            document_id=document_id,
            message=f"File {file_path} processed. {len(chunk_ids)} chunks upserted",
            chunks_processed=len(chunk_ids),
        )
    except MetadataProcessingError as e:
        await db.rollback()
        raise MetadataProcessingError(f"Failed to parse metadata for file {file_path}") from e
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e


@router.post("/text/", response_model=FileProcessingResponse)
async def process_text_file_change(event: TextFileChangeEvent, db: AsyncSession = Depends(get_db)):
    """
    Process text-based file changes (markdown, txt, etc.).
    Content is sent as plain text.
    """
    # Convert text content to bytes for processor
    content_bytes = event.file_content.encode("utf-8")
    return await _process_file_content(
        file_path=event.file_path, content_bytes=content_bytes, metadata=event.metadata, db=db
    )


@router.post("/binary/", response_model=FileProcessingResponse)
async def process_binary_file_change(
    event: BinaryFileChangeEvent, db: AsyncSession = Depends(get_db)
):
    """
    Process binary file changes (PDFs, images, etc.).
    Content is sent as base64-encoded string and automatically decoded to bytes.
    """
    # event.file_content is already bytes thanks to the validator
    return await _process_file_content(
        file_path=event.file_path, content_bytes=event.file_content, metadata=event.metadata, db=db
    )


@router.delete("/", response_model=FileProcessingResponse)
async def delete_file(
    file_path: str = Query(..., description="Path to the file to delete from the database"),
    db: AsyncSession = Depends(get_db),
):
    # Try to find document
    if await delete_document(db, file_path):
        await db.commit()
        return FileProcessingResponse(
            message=f"Document '{file_path}' and its associated chunks deleted",
        )
    else:
        return FileProcessingResponse(message="No document found, nothing deleted")
