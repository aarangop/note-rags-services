"""
API endpoint tests for the unified file events processing endpoint.

These tests use FastAPI's test client to test the actual HTTP endpoint behavior,
mocking only essential external dependencies while testing realistic request/response flows.
"""

import base64
from unittest.mock import AsyncMock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient
from note_rags_db import get_async_db_session


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
    app.dependency_overrides[get_async_db_session] = lambda: mock_db
    yield TestClient(app)
    # Clean up
    app.dependency_overrides = {}


class TestFileEventsAPI:
    """Test the unified file change processing API endpoint using HTTP requests."""

    def test_markdown_file_with_plain_text_content(self, client):
        """Test processing a markdown file with plain text content."""
        # Arrange - Real markdown content as plain text
        markdown_content = """# Test Document

This is a test markdown document with some content.

## Section 1
Content for section 1.

## Section 2
Content for section 2.
"""

        payload = {
            "event_type": "modified",
            "file_content": markdown_content,  # Send as plain text
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Mock only the essential external dependencies
        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            # Configure mocks for successful processing
            mock_split_text.return_value = ["chunk1", "chunk2", "chunk3"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
            mock_upsert_document.return_value = 42
            mock_upsert_chunks.return_value = [101, 102, 103]
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = [
                {"id": 101, "content": "chunk1"},
                {"id": 102, "content": "chunk2"},
                {"id": 103, "content": "chunk3"},
            ]

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 42
            assert data["chunks_processed"] == 3
            assert "processed successfully" in data["message"]
            assert "/documents/test.md" in data["message"]

    def test_pdf_file_with_base64_content(self, client):
        """Test processing a PDF file with base64-encoded content."""
        # Arrange - Simulate PDF content encoded as base64
        fake_pdf_content = b"%PDF-1.4\nFake PDF content for testing"
        encoded_content = base64.b64encode(fake_pdf_content).decode()

        payload = {
            "event_type": "created",
            "file_content": encoded_content,  # Send as base64 encoded string
            "file_path": "/documents/test.pdf",
            "timestamp": "2024-01-15T10:30:00",
            "metadata": {"author": "test_user"},
        }

        # Mock dependencies including file processor to avoid PDF parsing issues
        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.FileProcessorRegistry.get_processor") as mock_get_processor,
        ):
            # Mock PDF processor to return extracted text
            mock_processor = mock_get_processor.return_value
            mock_processor.parse_content.return_value = (
                "Extracted text from PDF document",
                {"pages": 1, "format": "PDF"},
            )

            # Configure other mocks
            mock_split_text.return_value = ["pdf_chunk1", "pdf_chunk2"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_upsert_document.return_value = 123
            mock_upsert_chunks.return_value = [201, 202]
            mock_get_document.return_value = None
            mock_create_chunks.return_value = [
                {"id": 201, "content": "pdf_chunk1"},
                {"id": 202, "content": "pdf_chunk2"},
            ]

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 123
            assert data["chunks_processed"] == 2
            assert "processed successfully" in data["message"]

    def test_file_with_bytes_encoded_as_base64(self, client):
        """Test processing a file where bytes are base64 encoded (normal case)."""
        # Arrange - Simulate how bytes would be sent via JSON (base64 encoded)
        text_content = "This is plain text content."
        encoded_content = base64.b64encode(text_content.encode("utf-8")).decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,  # Base64 encoded
            "file_path": "/documents/test.md",  # Use .md since .txt is not supported
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            mock_split_text.return_value = ["single_chunk"]
            mock_get_embeddings.return_value = [[0.5, 0.5]]
            mock_upsert_document.return_value = 456
            mock_upsert_chunks.return_value = [301]
            mock_get_document.return_value = None
            mock_create_chunks.return_value = [{"id": 301, "content": "single_chunk"}]

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 456
            assert data["chunks_processed"] == 1

    def test_unsupported_file_type_returns_400(self, client):
        """Test that unsupported file types return 400 error."""
        # Arrange
        payload = {
            "event_type": "created",
            "file_content": "Some content",
            "file_path": "/documents/unsupported.xyz",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Act
        response = client.post("/file_events/", json=payload)

        # Assert
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
        assert "/documents/unsupported.xyz" in response.json()["detail"]

    def test_empty_file_processing(self, client):
        """Test processing of empty file content."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": "",  # Empty content
            "file_path": "/documents/empty.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            # Empty content results in no chunks
            mock_split_text.return_value = []
            mock_get_embeddings.return_value = []
            mock_upsert_document.return_value = 99
            mock_upsert_chunks.return_value = []
            mock_get_document.return_value = None
            mock_create_chunks.return_value = []

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 99
            assert data["chunks_processed"] == 0
            assert "processed successfully" in data["message"]

    def test_file_unchanged_skips_processing(self, client):
        """Test that unchanged files are skipped."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": "Same content as before",
            "file_path": "/documents/unchanged.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.check_document_changed") as mock_check_changed,
        ):
            # Mock existing document that hasn't changed
            mock_document = AsyncMock()
            mock_document.id = 789
            mock_get_document.return_value = mock_document
            mock_check_changed.return_value = False  # Document unchanged

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 789
            assert data["chunks_processed"] == 0
            assert "unchanged" in data["message"]

    def test_unicode_content_handling(self, client):
        """Test processing files with unicode characters."""
        # Arrange
        unicode_content = """# Document with Unicode

Content with émojis 🎉 and special chars: àáâãäåæç

## Math Symbols
∑ ∞ ≠ ≤ ≥ π α β γ δ

## Chinese
你好世界
"""

        payload = {
            "event_type": "created",
            "file_content": unicode_content,
            "file_path": "/documents/unicode.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            mock_split_text.return_value = ["unicode_chunk"]
            mock_get_embeddings.return_value = [[0.7, 0.8, 0.9]]
            mock_upsert_document.return_value = 999
            mock_upsert_chunks.return_value = [501]
            mock_get_document.return_value = None
            mock_create_chunks.return_value = [{"id": 501, "content": "unicode_chunk"}]

            # Act - Should handle unicode without errors
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 999
            assert data["chunks_processed"] == 1

    def test_latin1_encoded_content_handling(self, client):
        """Test processing files with Latin-1 encoding (like the µ character)."""
        # Arrange - Content with Latin-1 characters that would cause UTF-8 errors
        latin1_content = "# Document with Latin-1\n\nThis has a µ (micro) symbol and other Latin-1 chars: àáâãäåæç"
        # Encode as Latin-1 then base64 encode for transmission
        latin1_bytes = latin1_content.encode("latin-1")
        encoded_content = base64.b64encode(latin1_bytes).decode("ascii")

        payload = {
            "event_type": "created",
            "file_content": encoded_content,
            "file_path": "/documents/latin1.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            mock_split_text.return_value = ["latin1_chunk"]
            mock_get_embeddings.return_value = [[0.1, 0.2, 0.3]]
            mock_upsert_document.return_value = 888
            mock_upsert_chunks.return_value = [601]
            mock_get_document.return_value = None
            mock_create_chunks.return_value = [{"id": 601, "content": "latin1_chunk"}]

            # Act - Should handle Latin-1 encoding without errors
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 888
            assert data["chunks_processed"] == 1

    def test_embedding_service_error_raises_exception(self, client):
        """Test that embedding service errors raise an exception."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": "Test content",
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_upsert_document.return_value = 100
            mock_get_document.return_value = None
            mock_get_embeddings.side_effect = Exception("Embedding service unavailable")

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                client.post("/file_events/", json=payload)

            assert "Embedding service unavailable" in str(exc_info.value)

    def test_database_error_raises_exception(self, client):
        """Test that database errors raise an exception."""
        # Arrange
        payload = {
            "event_type": "modified",
            "file_content": "Test content",
            "file_path": "/documents/test.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.return_value = [[0.1, 0.2]]
            mock_get_document.return_value = None
            mock_upsert_document.side_effect = Exception("Database connection failed")

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                client.post("/file_events/", json=payload)

            assert "Database connection failed" in str(exc_info.value)

    def test_invalid_json_payload_returns_422(self, client):
        """Test that invalid JSON payload returns 422 validation error."""
        # Arrange - Missing required fields
        invalid_payload = {
            "event_type": "modified",
            # Missing file_content, file_path
        }

        # Act
        response = client.post("/file_events/", json=invalid_payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_delete_file_endpoint(self, client):
        """Test the file deletion endpoint."""
        # Arrange
        file_path = "/documents/to_delete.md"

        with patch("app.routes.events.delete_document") as mock_delete:
            mock_delete.return_value = True  # Successful deletion

            # Act
            response = client.delete(f"/file_events/?file_path={file_path}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "deleted" in data["message"]
            assert file_path in data["message"]

    def test_delete_nonexistent_file(self, client):
        """Test deleting a file that doesn't exist."""
        # Arrange
        file_path = "/documents/nonexistent.md"

        with patch("app.routes.events.delete_document") as mock_delete:
            mock_delete.return_value = False  # File not found

            # Act
            response = client.delete(f"/file_events/?file_path={file_path}")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "No document found" in data["message"]

    def test_large_file_processing(self, client):
        """Test processing of large file content."""
        # Arrange - Create large content
        large_content = "# Large Document\n\n" + "This is a paragraph with content. " * 500

        payload = {
            "event_type": "modified",
            "file_content": large_content,
            "file_path": "/documents/large.md",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            # Simulate many chunks from large content
            num_chunks = 25
            chunks = [f"chunk_{i}" for i in range(num_chunks)]
            embeddings = [[float(i % 10)] * 5 for i in range(num_chunks)]
            chunk_ids = list(range(1, num_chunks + 1))

            mock_split_text.return_value = chunks
            mock_get_embeddings.return_value = embeddings
            mock_upsert_document.return_value = 500
            mock_upsert_chunks.return_value = chunk_ids
            mock_get_document.return_value = None
            mock_create_chunks.return_value = [
                {"id": i, "content": f"chunk_{i - 1}"} for i in chunk_ids
            ]

            # Act
            response = client.post("/file_events/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 500
            assert data["chunks_processed"] == num_chunks
