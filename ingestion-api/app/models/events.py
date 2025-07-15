from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"

class BaseFileChangeEvent(BaseModel):
    event_type: EventType
    file_path: str
    timestamp: datetime | None = None

class FileChangeEvent(BaseFileChangeEvent):
    file_content: bytes
    metadata: dict[str, Any] | None = None
    file_size: int | None = Field(default=None, description="Size of the file in bytes")
    checksum: str | None = Field(default=None, description="SHA256 checksum of file content")


class FileDeletedEvent(BaseFileChangeEvent):
    pass
