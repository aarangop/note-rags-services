"""Response model for API endpoints."""

from typing import Optional
from pydantic import BaseModel


class FileProcessingResponse(BaseModel):
    """Response model for file processing endpoint."""
    message: str
    document_id: Optional[int] = None
    chunks_processed: Optional[int] = None
