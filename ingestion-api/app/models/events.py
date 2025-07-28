import base64
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class BaseFileChangeEvent(BaseModel):
    event_type: EventType
    file_path: str
    timestamp: datetime | None = None


# For text-based files (markdown, txt, etc.)
class TextFileChangeEvent(BaseFileChangeEvent):
    """For text-based files that can be sent as plain text."""

    file_content: str  # Plain text content
    metadata: dict[str, Any] | None = None
    file_size: int | None = Field(default=None, description="Size of the file in bytes")
    checksum: str | None = Field(default=None, description="SHA256 checksum of file content")


# For binary files (PDFs, images, etc.)
class BinaryFileChangeEvent(BaseFileChangeEvent):
    """For binary files that must be base64 encoded."""

    file_content: bytes  # Will be base64 decoded automatically
    metadata: dict[str, Any] | None = None
    file_size: int | None = Field(default=None, description="Size of the file in bytes")
    checksum: str | None = Field(default=None, description="SHA256 checksum of file content")

    @field_validator("file_content", mode="before")
    @classmethod
    def decode_base64_content(cls, v):
        """Convert base64-encoded string to bytes."""
        if isinstance(v, str):
            try:
                return base64.b64decode(v)
            except Exception:
                # If it's not valid base64, just encode as UTF-8
                return v.encode("utf-8")
        return v


class FileDeletedEvent(BaseFileChangeEvent):
    pass
