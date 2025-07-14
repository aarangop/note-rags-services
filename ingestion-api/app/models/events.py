from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class FileChangeEvent(BaseModel):
    event_type: EventType
    file_content: bytes
    file_path: str
    timestamp: datetime | None

    metadata: dict[str, Any] | None = None

    file_size: int | None = Field(default=None, description="Size of the file in bytes")

    checksum: str | None = Field(default=None, description="SHA256 checksum of file content")
