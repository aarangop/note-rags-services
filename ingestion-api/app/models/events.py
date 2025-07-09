from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


class FileChangeEvent(BaseModel):
    event_type: EventType
    file_content: bytes
    file_path: str
    timestamp: Optional[datetime]

    metadata: Optional[Dict[str, Any]] = None

    file_size: Optional[int] = Field(
        default=None, description="Size of the file in bytes"
    )

    checksum: Optional[str] = Field(
        default=None, description="SHA256 checksum of file content"
    )
