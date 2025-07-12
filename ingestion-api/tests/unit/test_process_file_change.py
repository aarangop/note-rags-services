"""
Unit tests for the process_file_change API endpoint.

These tests focus on the public API and use proper mocking to isolate
the function under test from its dependencies.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.events import EventType, FileChangeEvent
from app.routes.events import process_file_change
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


class TestProcessFileChange:
    """Test class for the process_file_change function."""

    @pytest.mark.asyncio
    async def test_successful_file_processing(
        self,
        mock_db_session: AsyncSession,
        sample_file_change_event: FileChangeEvent,
        sample_text_chunks: list,
        sample_embeddings: list,
        sample_document_chunks: list,
    ):
        """Test successful processing of a file change event."""
        # Arrange
        mock_processor = Mock()
        mock_processor.extract_text.return_value = (
            "Extracted text content",
            {"key": "value"},
        )

        expected_document_id = 123
        expected_chunk_ids = [1, 2, 3]

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            # Configure mocks
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = sample_text_chunks
            mock_get_embeddings.return_value = sample_embeddings
            mock_upsert_document.return_value = expected_document_id
            mock_create_chunks.return_value = sample_document_chunks
            mock_upsert_chunks.return_value = expected_chunk_ids

            # Act
            result = await process_file_change(sample_file_change_event, mock_db_session)

            # Assert
            assert result == {
                "message": f"File {sample_file_change_event.file_path} processed. {len(expected_chunk_ids)} chunks upserted",
                "document_id": expected_document_id,
            }

            # Verify all mocks were called correctly
            mock_registry.get_processor.assert_called_once_with(sample_file_change_event.file_path)
            mock_processor.extract_text.assert_called_once_with(
                sample_file_change_event.file_content
            )
            mock_split_text.assert_called_once_with("Extracted text content")
            mock_get_embeddings.assert_called_once_with(sample_text_chunks)
            mock_upsert_document.assert_called_once_with(
                db=mock_db_session,
                content="Extracted text content",
                file_path=sample_file_change_event.file_path,
                metadata={"key": "value"},
            )
            mock_create_chunks.assert_called_once_with(
                embeddings=sample_embeddings,
                text=sample_text_chunks,
                document_id=expected_document_id,
            )
            mock_upsert_chunks.assert_called_once_with(
                db=mock_db_session,
                document_id=expected_document_id,
                chunks=sample_document_chunks,
            )

    @pytest.mark.asyncio
    async def test_unsupported_file_type_raises_http_exception(self, mock_db_session: AsyncSession):
        """Test that unsupported file types raise HTTPException with 400 status."""
        # Arrange
        unsupported_event = FileChangeEvent(
            event_type=EventType.CREATED,
            file_content=b"unsupported content",
            file_path="/path/to/unsupported.xyz",
            timestamp=datetime.now(),
        )

        with patch("app.routes.events.FileProcessorRegistry") as mock_registry:
            mock_registry.get_processor.side_effect = ValueError("Unsupported file type")

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await process_file_change(unsupported_event, mock_db_session)

            assert exc_info.value.status_code == 400
            assert "not supported" in exc_info.value.detail
            assert unsupported_event.file_path in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_pdf_file_processing(
        self, mock_db_session: AsyncSession, sample_pdf_event: FileChangeEvent
    ):
        """Test processing of PDF files specifically."""
        # Arrange
        mock_processor = Mock()
        extracted_text = "PDF content extracted successfully"
        pdf_metadata = {"pages": 5, "title": "Test PDF"}
        mock_processor.extract_text.return_value = (extracted_text, pdf_metadata)

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = ["PDF chunk 1", "PDF chunk 2"]
            mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_upsert_document.return_value = 456
            mock_create_chunks.return_value = [{"id": 1}, {"id": 2}]
            mock_upsert_chunks.return_value = [10, 11]

            # Act
            result = await process_file_change(sample_pdf_event, mock_db_session)

            # Assert
            assert result["document_id"] == 456
            assert "2 chunks upserted" in result["message"]

            # Verify PDF-specific processing
            mock_processor.extract_text.assert_called_once_with(sample_pdf_event.file_content)
            mock_upsert_document.assert_called_once_with(
                db=mock_db_session,
                content=extracted_text,
                file_path=sample_pdf_event.file_path,
                metadata=pdf_metadata,
            )

    @pytest.mark.asyncio
    async def test_empty_file_content(self, mock_db_session: AsyncSession):
        """Test processing of files with empty content."""
        # Arrange
        empty_event = FileChangeEvent(
            event_type=EventType.MODIFIED,
            file_content=b"",
            file_path="/path/to/empty.txt",
            timestamp=datetime.now(),
        )

        mock_processor = Mock()
        mock_processor.extract_text.return_value = ("", {})

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = []  # No chunks from empty content
            mock_get_embeddings.return_value = []
            mock_upsert_document.return_value = 789
            mock_create_chunks.return_value = []
            mock_upsert_chunks.return_value = []

            # Act
            result = await process_file_change(empty_event, mock_db_session)

            # Assert
            assert result["document_id"] == 789
            assert "0 chunks upserted" in result["message"]

    @pytest.mark.asyncio
    async def test_large_file_with_many_chunks(
        self, mock_db_session: AsyncSession, sample_file_change_event: FileChangeEvent
    ):
        """Test processing of large files that generate many chunks."""
        # Arrange
        mock_processor = Mock()
        large_text = "Large document content " * 1000
        mock_processor.extract_text.return_value = (large_text, {"size": "large"})

        # Simulate many chunks
        many_chunks = [f"Chunk {i}" for i in range(50)]
        many_embeddings = [[float(i)] * 5 for i in range(50)]
        many_chunk_objects = [{"id": i, "text": f"Chunk {i}"} for i in range(50)]
        many_chunk_ids = list(range(1, 51))

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = many_chunks
            mock_get_embeddings.return_value = many_embeddings
            mock_upsert_document.return_value = 999
            mock_create_chunks.return_value = many_chunk_objects
            mock_upsert_chunks.return_value = many_chunk_ids

            # Act
            result = await process_file_change(sample_file_change_event, mock_db_session)

            # Assert
            assert result["document_id"] == 999
            assert "50 chunks upserted" in result["message"]

            # Verify that all services were called with the correct large data
            mock_get_embeddings.assert_called_once_with(many_chunks)
            mock_create_chunks.assert_called_once_with(
                embeddings=many_embeddings, text=many_chunks, document_id=999
            )

    @pytest.mark.asyncio
    async def test_file_with_complex_metadata(self, mock_db_session: AsyncSession):
        """Test processing files with complex metadata."""
        # Arrange
        complex_metadata = {
            "author": "John Doe",
            "created_date": "2024-01-15",
            "tags": ["document", "test", "api"],
            "nested": {"version": 1, "format": "text"},
        }

        event_with_metadata = FileChangeEvent(
            event_type=EventType.CREATED,
            file_content=b"Content with metadata",
            file_path="/path/to/metadata_file.txt",
            timestamp=datetime.now(),
            metadata=complex_metadata,
        )

        mock_processor = Mock()
        extracted_metadata = {"extracted_info": "from_processor"}
        mock_processor.extract_text.return_value = ("Text content", extracted_metadata)

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.return_value = [[0.1]]
            mock_upsert_document.return_value = 111
            mock_create_chunks.return_value = [{"id": 1}]
            mock_upsert_chunks.return_value = [1]

            # Act
            result = await process_file_change(event_with_metadata, mock_db_session)

            # Assert
            assert result["document_id"] == 111

            # Verify that the extracted metadata (not event metadata) was used
            mock_upsert_document.assert_called_once_with(
                db=mock_db_session,
                content="Text content",
                file_path=event_with_metadata.file_path,
                metadata=extracted_metadata,  # This should be from processor, not event
            )

    @pytest.mark.asyncio
    async def test_database_session_passed_correctly(
        self, sample_file_change_event: FileChangeEvent
    ):
        """Test that the database session is passed correctly to all database operations."""
        # Arrange
        custom_db_session = AsyncMock(spec=AsyncSession)
        mock_processor = Mock()
        mock_processor.extract_text.return_value = ("content", {})

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
            patch("app.routes.events.upsert_document") as mock_upsert_document,
            patch("app.routes.events.create_document_chunks") as mock_create_chunks,
            patch("app.routes.events.upsert_document_chunks") as mock_upsert_chunks,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.return_value = [[0.1]]
            mock_upsert_document.return_value = 222
            mock_create_chunks.return_value = [{"id": 1}]
            mock_upsert_chunks.return_value = [1]

            # Act
            await process_file_change(sample_file_change_event, custom_db_session)

            # Assert that the custom session was passed to database operations
            mock_upsert_document.assert_called_once()
            call_args = mock_upsert_document.call_args
            assert call_args.kwargs["db"] is custom_db_session

            mock_upsert_chunks.assert_called_once()
            call_args = mock_upsert_chunks.call_args
            assert call_args.kwargs["db"] is custom_db_session

    @pytest.mark.asyncio
    async def test_error_propagation_from_dependencies(
        self, mock_db_session: AsyncSession, sample_file_change_event: FileChangeEvent
    ):
        """Test that errors from dependencies are properly propagated."""
        # Test error from get_embeddings
        mock_processor = Mock()
        mock_processor.extract_text.return_value = ("content", {})

        with (
            patch("app.routes.events.FileProcessorRegistry") as mock_registry,
            patch("app.routes.events.split_text") as mock_split_text,
            patch("app.routes.events.get_embeddings") as mock_get_embeddings,
        ):
            mock_registry.get_processor.return_value = mock_processor
            mock_split_text.return_value = ["chunk"]
            mock_get_embeddings.side_effect = Exception("Embedding service error")

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await process_file_change(sample_file_change_event, mock_db_session)

            assert "Embedding service error" in str(exc_info.value)
