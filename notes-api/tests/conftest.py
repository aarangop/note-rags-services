from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
from app.main import app
from app.models.document import DocumentType
from app.models.note import Note, NoteCreate, NoteUpdate
from fastapi.testclient import TestClient
from note_rags_db.schemas import Document
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session():
    """Mock database session for testing with common database operations"""
    mock_session = AsyncMock(spec=AsyncSession)

    # Set up default behaviors
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.close = AsyncMock()

    return mock_session


@pytest.fixture
def test_client_with_db_mock(mock_db_session):
    """FastAPI test client with database dependency overridden"""
    from note_rags_db import get_async_db_session

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_async_db_session] = override_get_db

    with TestClient(app) as client:
        yield client, mock_db_session

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_client():
    """FastAPI test client without database mocking for simpler tests"""
    return TestClient(app)


@pytest.fixture
def sample_note_create():
    """Sample NoteCreate object for testing"""
    return NoteCreate(
        file_path="/test/note.md",
        title="Test Note",
        content="This is a test note content",
        document_type=DocumentType.NOTE,
        metadata={"tags": ["test", "sample"]},
    )


@pytest.fixture
def sample_note_update():
    """Sample NoteUpdate object for testing"""
    return NoteUpdate(
        title="Updated Test Note",
        content="This is updated test note content",
        metadata={"tags": ["test", "updated"]},
    )


@pytest.fixture
def sample_document():
    """Sample Document object for testing"""
    return Document(
        id=1,
        title="Test Note",
        file_path="/test/note.md",
        content="This is a test note content",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        content_hash="test_hash",
        document_type="note",
        document_metadata={"tags": ["test", "sample"]},
    )


@pytest.fixture
def sample_note_response():
    """Sample NoteResponse object for testing"""
    return Note(
        id=123,
        file_path="/test/note.md",
        title="Test Note",
        content="This is a test note content",
        document_type=DocumentType.NOTE,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        metadata={"tags": ["test", "sample"]},
    )
