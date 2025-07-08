"""
Shared test fixtures and utilities.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.events import EventType, FileChangeEvent


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def sample_file_change_event() -> FileChangeEvent:
    """Create a sample FileChangeEvent for testing."""
    return FileChangeEvent(
        event_type=EventType.MODIFIED,
        file_content=b"This is sample file content for testing.",
        file_path="/path/to/test/document.txt",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        metadata={"file_size": 42, "author": "test_user"},
    )


@pytest.fixture
def sample_pdf_event() -> FileChangeEvent:
    """Create a sample PDF FileChangeEvent for testing."""
    return FileChangeEvent(
        event_type=EventType.CREATED,
        file_content=b"%PDF-1.4 fake pdf content",
        file_path="/path/to/test/document.pdf",
        timestamp=datetime(2024, 1, 15, 11, 0, 0),
        metadata={"file_size": 1024},
    )


@pytest.fixture
def sample_text_chunks():
    """Sample text chunks for testing."""
    return [
        "This is the first chunk of text.",
        "This is the second chunk of text.",
        "This is the third chunk of text.",
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [
        [0.1, 0.2, 0.3, 0.4, 0.5],
        [0.6, 0.7, 0.8, 0.9, 1.0],
        [1.1, 1.2, 1.3, 1.4, 1.5],
    ]


@pytest.fixture
def sample_document_chunks():
    """Sample document chunks for testing."""
    return [
        {"id": 1, "text": "chunk 1", "embedding": [0.1, 0.2, 0.3]},
        {"id": 2, "text": "chunk 2", "embedding": [0.4, 0.5, 0.6]},
        {"id": 3, "text": "chunk 3", "embedding": [0.7, 0.8, 0.9]},
    ]
