"""Response model for API endpoints."""

from pydantic import BaseModel


class FileProcessingResponse(BaseModel):
    """Response model for file processing endpoint."""

    document_id: int
    message: str
    chunks_processed: int
