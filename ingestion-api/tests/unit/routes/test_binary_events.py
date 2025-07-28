"""
API endpoint tests for the new binary file processing endpoint.

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


class TestBinaryFileEventsAPI:
    """Test the binary file change processing API endpoint using HTTP requests."""

    def test_successful_pdf_processing(self, client):
        """Test successful processing of a PDF file via HTTP API."""
        # Arrange - Simulate PDF content
        fake_pdf_content = b"%PDF-1.4\nFake PDF content for testing"

        # Encode content as base64 (as would be done by client)
        encoded_content = base64.b64encode(fake_pdf_content).decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,  # Send as base64 encoded string
            "file_path": "/documents/test.pdf",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Mock external dependencies
        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.FileProcessorRegistry.get_processor") as mock_get_processor,
        ):
            # Mock PDF processor
            mock_processor = mock_get_processor.return_value
            mock_processor.parse_content.return_value = (
                "Extracted PDF content from test file",
                {"pages": 1},
            )

            # Configure mocks
            mock_split_text.return_value = ["pdf_chunk1", "pdf_chunk2"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_upsert_document.return_value = 42
            mock_upsert_chunks.return_value = [101, 102]
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = [
                {"id": 101, "content": "pdf_chunk1"},
                {"id": 102, "content": "pdf_chunk2"},
            ]

            # Act
            response = client.post("/file_events/binary/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 42
            assert data["chunks_processed"] == 2
            assert "message" in data
            assert "/documents/test.pdf" in data["message"]

    def test_markdown_via_binary_endpoint(self, client):
        """Test that markdown can also be processed via binary endpoint (for flexibility)."""
        # Arrange - Real markdown content
        markdown_content = """# Test Document

This is a test markdown document with some content.

## Section 1
Content for section 1.
"""

        # Encode as base64 (as would be done for binary endpoint)
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
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.FileProcessorRegistry.get_processor") as mock_get_processor,
        ):
            # Mock markdown processor (for .md file)
            mock_processor = mock_get_processor.return_value
            mock_processor.parse_content.return_value = (
                "# Test Document\n\nThis is a test markdown document with some content.\n\n## Section 1\nContent for section 1.",
                {},
            )

            # Configure mocks
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
            response = client.post("/file_events/binary/", json=payload)

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
        fake_content = b"Some binary content"
        encoded_content = base64.b64encode(fake_content).decode()

        payload = {
            "event_type": "created",
            "file_content": encoded_content,
            "file_path": "/documents/unsupported.xyz",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Act
        response = client.post("/file_events/binary/", json=payload)

        # Assert
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
        assert "/documents/unsupported.xyz" in response.json()["detail"]

    def test_invalid_base64_content(self, client):
        """Test handling of invalid base64 content."""
        # Arrange - Invalid base64 string
        payload = {
            "event_type": "modified",
            "file_content": "This is not valid base64!@#$%",
            "file_path": "/documents/test.pdf",
            "timestamp": "2024-01-15T10:30:00",
        }

        # Mock external dependencies
        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.FileProcessorRegistry.get_processor") as mock_get_processor,
        ):
            # Mock PDF processor
            mock_processor = mock_get_processor.return_value
            mock_processor.parse_content.return_value = ("This is not valid base64!@#$%", {})

            # Configure mocks
            mock_split_text.return_value = ["chunk1"]
            mock_get_embeddings.return_value = [[0.1, 0.2]]
            mock_upsert_document.return_value = 42
            mock_upsert_chunks.return_value = [101]
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = [{"id": 101, "content": "chunk1"}]

            # Act - Should handle gracefully by treating as UTF-8 text
            response = client.post("/file_events/binary/", json=payload)

            # Assert - Should succeed (fallback to UTF-8 encoding)
            assert response.status_code == 200

    def test_empty_binary_file_processing(self, client):
        """Test processing of empty binary file."""
        # Arrange
        encoded_content = base64.b64encode(b"").decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,
            "file_path": "/documents/empty.pdf",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.FileProcessorRegistry.get_processor") as mock_get_processor,
        ):
            # Mock PDF processor for empty content
            mock_processor = mock_get_processor.return_value
            mock_processor.parse_content.return_value = ("", {})  # Empty content

            # Empty content results in no chunks
            mock_split_text.return_value = []
            mock_get_embeddings.return_value = []
            mock_upsert_document.return_value = 99
            mock_upsert_chunks.return_value = []
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = []

            # Act
            response = client.post("/file_events/binary/", json=payload)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == 99
            assert data["chunks_processed"] == 0
            assert "message" in data
            assert "/documents/empty.pdf" in data["message"]

    def test_embedding_service_error_returns_500(self, client):
        """Test that embedding service errors return 500 status."""
        # Arrange
        fake_content = b"Some PDF content"
        encoded_content = base64.b64encode(fake_content).decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,
            "file_path": "/documents/test.pdf",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_upsert_document.return_value = 100
            mock_get_embeddings.side_effect = Exception("Embedding service unavailable")
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = []

            # Act
            response = client.post("/file_events/binary/", json=payload)

            # Assert
            assert response.status_code == 500

    def test_database_error_returns_500(self, client):
        """Test that database errors return 500 status."""
        # Arrange
        fake_content = b"Some PDF content"
        encoded_content = base64.b64encode(fake_content).decode()

        payload = {
            "event_type": "modified",
            "file_content": encoded_content,
            "file_path": "/documents/test.pdf",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
        ):
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.return_value = [[0.1, 0.2]]
            mock_upsert_document.side_effect = Exception("Database connection failed")
            mock_get_document.return_value = None  # No existing document
            mock_create_chunks.return_value = []

            # Act
            response = client.post("/file_events/binary/", json=payload)

            # Assert
            assert response.status_code == 500
