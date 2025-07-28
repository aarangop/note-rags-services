"""
Shared test fixtures and utilities.
"""

import base64
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from app.models.events import BinaryFileChangeEvent, EventType, TextFileChangeEvent
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def sample_text_file_event() -> TextFileChangeEvent:
    """Create a sample TextFileChangeEvent for testing."""
    return TextFileChangeEvent(
        event_type=EventType.MODIFIED,
        file_content="This is sample file content for testing.",
        file_path="/path/to/test/document.txt",
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
    )


@pytest.fixture
def sample_binary_file_event() -> BinaryFileChangeEvent:
    """Create a sample BinaryFileChangeEvent for testing."""
    # Base64 encode the binary content
    pdf_content = b"%PDF-1.4 fake pdf content"
    encoded_content = base64.b64encode(pdf_content).decode()

    # Create the event with the base64 string - the field validator will convert it to bytes
    event_data = {
        "event_type": EventType.CREATED,
        "file_content": encoded_content,  # This will be converted to bytes by the validator
        "file_path": "/path/to/test/document.pdf",
        "timestamp": datetime(2024, 1, 15, 11, 0, 0),
    }

    return BinaryFileChangeEvent(**event_data)


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
