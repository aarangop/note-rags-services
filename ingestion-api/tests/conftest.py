"""
Shared test fixtures and utilities.
"""

import base64
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from app.models.events import EventType, FileChangeEvent
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def sample_file_change_event() -> FileChangeEvent:
    """Create a sample FileChangeEvent for testing with text content."""
    # Use dict construction to work around type checker
    event_data = {
        "event_type": EventType.MODIFIED,
        "file_content": "This is sample file content for testing.",  # String -> bytes via validator
        "file_path": "/path/to/test/document.md",  # Use .md since it's supported
        "timestamp": datetime(2024, 1, 15, 10, 30, 0),
    }
    return FileChangeEvent(**event_data)


@pytest.fixture
def sample_binary_file_event() -> FileChangeEvent:
    """Create a sample FileChangeEvent for testing with binary (base64) content."""
    # Base64 encode the binary content
    pdf_content = b"%PDF-1.4 fake pdf content"
    encoded_content = base64.b64encode(pdf_content).decode()

    # Use dict construction to work around type checker
    event_data = {
        "event_type": EventType.CREATED,
        "file_content": encoded_content,  # Base64 string -> bytes via validator
        "file_path": "/path/to/test/document.pdf",
        "timestamp": datetime(2024, 1, 15, 11, 0, 0),
    }

    return FileChangeEvent(**event_data)


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
