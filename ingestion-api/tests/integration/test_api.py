"""
Integration tests for the process_file_change endpoint.

These tests verify that the endpoint works correctly with FastAPI's test client.
"""

from unittest.mock import Mock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def valid_file_event_payload():
    """Valid payload for file change event."""
    return {
        "event_type": "modified",
        "file_content": "VGhpcyBpcyB0ZXN0IGZpbGUgY29udGVudA==",  # base64 encoded "This is test file content"
        "file_path": "/path/to/test.txt",
        "timestamp": "2024-01-15T10:30:00",
        "metadata": {"author": "test_user"},
    }


class TestProcessFileChangeEndpoint:
    """Integration tests for the file change processing endpoint."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_200_on_success(self, client, valid_file_event_payload):
        """Test that the endpoint returns 200 status on successful processing."""
        # Arrange - Mock all the dependencies
        mock_processor = Mock()
        mock_processor.parse_content.return_value = (
            "Extracted content",
            {"key": "value"},
        )

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.get_db") as mock_get_db,
        ):
            # Configure mocks
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = ["chunk1", "chunk2"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_upsert_document.return_value = 123
            mock_create_chunks.return_value = [{"id": 1}, {"id": 2}]
            mock_upsert_chunks.return_value = [1, 2]
            mock_get_document.return_value = None  # No existing document
            mock_get_db.return_value.__aenter__ = lambda self: mock_get_db.return_value
            mock_get_db.return_value.__aexit__ = lambda self, *args: None

            # Act
            response = client.post("/file_events/binary/", json=valid_file_event_payload)

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert "message" in response_data
            assert "document_id" in response_data
            assert response_data["document_id"] == 123
            assert "2 chunks upserted" in response_data["message"]

    @pytest.mark.asyncio
    async def test_endpoint_returns_400_on_unsupported_file(self, client):
        """Test that the endpoint returns 400 for unsupported file types."""
        # Arrange
        unsupported_payload = {
            "event_type": "created",
            "file_content": "dW5zdXBwb3J0ZWQgY29udGVudA==",  # base64 encoded "unsupported content"
            "file_path": "/path/to/unsupported.xyz",
            "timestamp": "2024-01-15T10:30:00",
        }

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.get_document_by_file_path") as mock_get_document,
            patch("app.routes.events.get_db") as mock_get_db,
        ):
            mock_registry.get_processor.side_effect = ValueError("Unsupported file type")
            mock_get_document.return_value = None  # No existing document
            mock_get_db.return_value.__aenter__ = lambda self: mock_get_db.return_value
            mock_get_db.return_value.__aexit__ = lambda self, *args: None

            # Act
            response = client.post("/file_events/binary/", json=unsupported_payload)

            # Assert
            assert response.status_code == 400
            assert "not supported" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_endpoint_validates_request_payload(self, client):
        """Test that the endpoint validates the request payload structure."""
        # Test missing required fields
        invalid_payloads = [
            {},  # Empty payload
            {"event_type": "modified"},  # Missing file_content, file_path, timestamp
            {
                "event_type": "invalid_type",
                "file_content": "Y29udGVudA==",
                "file_path": "/path/to/file.txt",
                "timestamp": "2024-01-15T10:30:00",
            },  # Invalid event_type
            {
                "event_type": "modified",
                "file_content": "Y29udGVudA==",
                "file_path": "/path/to/file.txt",
                "timestamp": "invalid-timestamp",
            },  # Invalid timestamp format
        ]

        for payload in invalid_payloads:
            response = client.post("/file_events/binary/", json=payload)
            assert response.status_code == 422  # Unprocessable Entity for validation errors

    @pytest.mark.asyncio
    async def test_endpoint_handles_different_event_types(self, client):
        """Test that the endpoint handles different event types correctly."""
        # Test different event types
        event_types = ["created", "modified", "deleted"]

        for event_type in event_types:
            payload = {
                "event_type": event_type,
                "file_content": "Y29udGVudA==",  # base64 encoded "content"
                "file_path": f"/path/to/{event_type}_file.txt",
                "timestamp": "2024-01-15T10:30:00",
            }

            # Mock all dependencies
            mock_processor = Mock()
            mock_processor.parse_content.return_value = (f"Content for {event_type}", {})

            with (
                patch("app.routes.events.FileProcessorRegistry") as mock_registry,
                patch("app.routes.events.split_text") as mock_split_text,
                patch("app.routes.events.get_embeddings") as mock_get_embeddings,
                patch("app.routes.events.upsert_document") as mock_upsert_document,
                patch("app.routes.events.create_document_chunks") as mock_create_chunks,
                patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
                patch("app.routes.events.get_document_by_file_path") as mock_get_document,
                patch("app.routes.events.get_db") as mock_get_db,
            ):
                mock_registry.get_processor.return_value = mock_processor
                mock_split_text.return_value = ["chunk"]
                mock_get_embeddings.return_value = [[0.1]]
                mock_upsert_document.return_value = 456
                mock_create_chunks.return_value = [{"id": 1}]
                mock_upsert_chunks.return_value = [1]
                mock_get_document.return_value = None  # No existing document
                mock_get_db.return_value.__aenter__ = lambda self: mock_get_db.return_value
                mock_get_db.return_value.__aexit__ = lambda self, *args: None

                response = client.post("/file_events/binary/", json=payload)

                # All event types should be processed successfully
                assert response.status_code == 200
                assert response.json()["document_id"] == 456
