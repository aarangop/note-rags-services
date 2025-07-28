import base64
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class FileChangeEvent(BaseModel):
    """Unified file change event for all file types."""

    event_type: EventType
    file_path: str
    file_content: bytes  # Always bytes - let processors handle interpretation
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None
    file_size: int | None = Field(default=None, description="Size of the file in bytes")
    checksum: str | None = Field(default=None, description="SHA256 checksum of file content")

    @field_validator("file_content", mode="before")
    @classmethod
    def ensure_bytes_content(cls, v):
        """
        Accept either bytes or base64-encoded string, convert to bytes.
        This provides flexibility for different client implementations.
        """
        if isinstance(v, bytes):
            return v
        elif isinstance(v, str):
            try:
                # Try to decode as base64 first
                return base64.b64decode(v)
            except Exception:
                # If not valid base64, assume it's plain text and encode
                return v.encode("utf-8")
        else:
            raise ValueError("file_content must be bytes or string")


class FileDeletedEvent(BaseModel):
    """Event for file deletion - no content needed."""

    event_type: EventType = Field(default=EventType.DELETED, frozen=True)
    file_path: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None
