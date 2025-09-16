"""Response model for API endpoints."""

from pydantic import BaseModel


class FileProcessingResponse(BaseModel):
    """Response model for file processing endpoint."""

    message: str
    document_id: int | None = None
    chunks_processed: int | None = None
