"""
API endpoint tests for the file change processing endpoint.

These tests use FastAPI's test client to test the actual HTTP endpoint behavior,
mocking only external dependencies while testing realistic request/response flows.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from app.db import get_db
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def client(mock_db):
    """Create a test client for the FastAPI app with mocked database."""
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    # Clean up
    app.dependency_overrides = {}


class TestFileEventsAPI:
    """Test the file change processing API endpoint using HTTP requests."""

    def test_successful_markdown_processing(self, client):
        """Test successful processing of a markdown file via HTTP API."""
        # Arrange - Real markdown content
        markdown_content = """# Test Document

This is a test markdown document with some content.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
"""

        # Encode content as base64 (as would be done by client)
        encoded_content = base64.b64encode(markdown_content.encode()).decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Mock external dependencies
        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            # Configure mocks
            mock_split_text.return_value = ["chunk1", "chunk2", "chunk3"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
            mock_upsert_document.return_value = 42
            mock_upsert_chunks.return_value = [101, 102, 103]

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 42
            assert data["chunks_processed"] == 3
            assert "message" in data
            assert "/documents/test.md" in data["message"]

    def test_unsupported_file_type_returns_400(self, client):
        """Test that unsupported file types return 400 error."""
        # Arrange
        payload = {
            "event_type": "created",
            "file_content": base64.b64encode(b"Some content").decode(),
            "file_path": "/documents/unsupported.xyz",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Act
        response = client.post("/file_events/", json=payload)

        # Assert
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
        assert "/documents/unsupported.xyz" in response.json()["detail"]

    def test_empty_markdown_file_processing(self, client):
        """Test processing of empty markdown file."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": base64.b64encode(b"").decode(),
            "file_path": "/documents/empty.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            # Empty content results in no chunks
            mock_split_text.return_value = []
            mock_get_embeddings.return_value = []
            mock_upsert_document.return_value = 99
            mock_upsert_chunks.return_value = []

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 99
            assert data["chunks_processed"] == 0
            assert "message" in data
            assert "/documents/empty.md" in data["message"]

    def test_large_markdown_file_processing(self, client):
        """Test processing of large markdown file that generates many chunks."""
        # Arrange
        large_content = "# Large Document\n\n" + "This is a paragraph with content. " * 100
        payload = {
            "event_type": "modified",
            "file_content": base64.b64encode(large_content.encode()).decode(),
            "file_path": "/documents/large.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            # Simulate many chunks from large content
            chunks = [f"chunk_{i}" for i in range(10)]
            embeddings = [[float(i)] * 5 for i in range(10)]
            chunk_ids = list(range(1, 11))

            mock_split_text.return_value = chunks
            mock_get_embeddings.return_value = embeddings
            mock_upsert_document.return_value = 500
            mock_upsert_chunks.return_value = chunk_ids

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 500
            assert data["chunks_processed"] == 10
            assert "message" in data
            assert "/documents/large.md" in data["message"]

    def test_markdown_with_special_characters(self, client):
        """Test processing markdown with unicode and special characters."""
        # Arrange
        special_content = """# Document with Special Characters

Content with unicode: émoji🎉 and symbols àáâã

## Code Block
```python
def hello():
    return "world"
```

## Math
E = mc²
"""

        payload = {
            "event_type": "created",
            "file_content": base64.b64encode(special_content.encode()).decode(),
            "file_path": "/documents/special.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            mock_split_text.return_value = ["special_chunk"]
            mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
            mock_upsert_document.return_value = 123
            mock_upsert_chunks.return_value = [456]

            # Act - Should not raise any encoding errors
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 123
            assert data["chunks_processed"] == 1
            assert "message" in data
            assert "/documents/special.md" in data["message"]

    def test_embedding_service_error_returns_500(self, client):
        """Test that embedding service errors return 500 status."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": base64.b64encode(b"# Test Document\n\nContent for testing.").decode(),
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_upsert_document.return_value = 100
            mock_get_embeddings.side_effect = Exception("Embedding service unavailable")

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 500

    def test_database_error_returns_500(self, client):
        """Test that database errors return 500 status."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": base64.b64encode(b"# Test Document\n\nContent for testing.").decode(),
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.return_value = [[0.1, 0.2]]
            mock_upsert_document.side_effect = Exception("Database connection failed")

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 500

    def test_invalid_json_payload_returns_422(self, client):
        """Test that invalid JSON payload returns 422 validation error."""
        # Arrange - Missing required fields
        invalid_payload = {
            "event_type": "modified",
            # Missing file_content, file_path, timestamp
        }

        # Act
        response = client.post("/file_events/", json=invalid_payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()
