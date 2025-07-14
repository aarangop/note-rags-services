"""
Unit tests for the document_service module.

These tests focus on testing the document service functions including
the new hash checking functionality for detecting document changes.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.services.document_service import (
    calculate_content_hash,
    check_document_changed,
    create_document_chunks,
    get_document_by_file_path,
    upsert_document,
    upsert_document_chunks,
)
from sqlalchemy.ext.asyncio import AsyncSession


class TestCalculateContentHash:
    """Test the calculate_content_hash function."""

    def test_calculate_content_hash_consistent(self):
        """Test that the same content produces the same hash."""
        content = "This is a test document content."
        hash1 = calculate_content_hash(content)
        hash2 = calculate_content_hash(content)
        assert hash1 == hash2

    def test_calculate_content_hash_different_content(self):
        """Test that different content produces different hashes."""
        content1 = "This is content A."
        content2 = "This is content B."
        hash1 = calculate_content_hash(content1)
        hash2 = calculate_content_hash(content2)
        assert hash1 != hash2

    def test_calculate_content_hash_empty_content(self):
        """Test hash calculation with empty content."""
        content = ""
        hash_result = calculate_content_hash(content)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA256 hex digest length

    def test_calculate_content_hash_unicode_content(self):
        """Test hash calculation with unicode content."""
        content = "This contains unicode: émojis 🎉 and símbolos"
        hash_result = calculate_content_hash(content)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_content_hash_large_content(self):
        """Test hash calculation with large content."""
        content = "Large content " * 10000
        hash_result = calculate_content_hash(content)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

    def test_calculate_content_hash_whitespace_sensitive(self):
        """Test that hash is sensitive to whitespace changes."""
        content1 = "Content with spaces"
        content2 = "Content  with  spaces"  # Different spacing
        hash1 = calculate_content_hash(content1)
        hash2 = calculate_content_hash(content2)
        assert hash1 != hash2


class TestCheckDocumentChanged:
    """Test the check_document_changed function."""

    def test_check_document_changed_no_change(self):
        """Test that unchanged content returns False."""
        content = "Original content"
        content_hash = calculate_content_hash(content)

        mock_document = Mock()
        mock_document.content_hash = content_hash

        result = check_document_changed(mock_document, content)
        assert result is False

    def test_check_document_changed_content_modified(self):
        """Test that modified content returns True."""
        original_content = "Original content"
        modified_content = "Modified content"
        original_hash = calculate_content_hash(original_content)

        mock_document = Mock()
        mock_document.content_hash = original_hash

        result = check_document_changed(mock_document, modified_content)
        assert result is True

    def test_check_document_changed_minor_change(self):
        """Test that even minor changes are detected."""
        original_content = "Content with period."
        modified_content = "Content with period!"  # Only punctuation change
        original_hash = calculate_content_hash(original_content)

        mock_document = Mock()
        mock_document.content_hash = original_hash

        result = check_document_changed(mock_document, modified_content)
        assert result is True

    def test_check_document_changed_empty_to_content(self):
        """Test change from empty to content."""
        original_content = ""
        modified_content = "New content"
        original_hash = calculate_content_hash(original_content)

        mock_document = Mock()
        mock_document.content_hash = original_hash

        result = check_document_changed(mock_document, modified_content)
        assert result is True

    def test_check_document_changed_content_to_empty(self):
        """Test change from content to empty."""
        original_content = "Some content"
        modified_content = ""
        original_hash = calculate_content_hash(original_content)

        mock_document = Mock()
        mock_document.content_hash = original_hash

        result = check_document_changed(mock_document, modified_content)
        assert result is True


class TestUpsertDocument:
    """Test the upsert_document function."""

    @pytest.mark.asyncio
    async def test_upsert_document_new_document(self):
        """Test creating a new document."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/new_document.txt"
        content = "New document content"
        metadata = {"author": "test"}

        with (
            patch("app.services.document_service.get_document_by_file_path") as mock_get_doc,
            patch("app.services.document_service.Document") as mock_document_class,
        ):
            # Document doesn't exist
            mock_get_doc.return_value = None

            # Mock document instance
            mock_document = Mock()
            mock_document.id = 123
            mock_document_class.return_value = mock_document

            result = await upsert_document(mock_db, file_path, content, metadata)

            assert result == 123
            mock_get_doc.assert_called_once_with(mock_db, file_path)
            mock_document_class.assert_called_once_with(
                file_path=file_path, content=content, content_hash=calculate_content_hash(content)
            )
            mock_db.add.assert_called_once_with(mock_document)
            mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_document_existing_unchanged(self):
        """Test updating an existing document with unchanged content."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/existing_document.txt"
        content = "Existing content"
        content_hash = calculate_content_hash(content)

        with patch("app.services.document_service.get_document_by_file_path") as mock_get_doc:
            # Document exists with same content
            mock_document = Mock()
            mock_document.id = 456
            mock_document.content_hash = content_hash
            mock_get_doc.return_value = mock_document

            result = await upsert_document(mock_db, file_path, content)

            assert result == 456
            # Should not add or flush since document unchanged
            mock_db.add.assert_not_called()
            mock_db.flush.assert_not_called()
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_document_existing_changed(self):
        """Test updating an existing document with changed content."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/existing_document.txt"
        old_content = "Old content"
        new_content = "New content"
        old_hash = calculate_content_hash(old_content)
        new_hash = calculate_content_hash(new_content)

        with (
            patch("app.services.document_service.get_document_by_file_path") as mock_get_doc,
            patch("app.services.document_service.delete"),
        ):
            # Document exists with different content
            mock_document = Mock()
            mock_document.id = 789
            mock_document.content_hash = old_hash
            mock_get_doc.return_value = mock_document

            result = await upsert_document(mock_db, file_path, new_content)

            assert result == 789
            assert mock_document.content == new_content
            assert mock_document.content_hash == new_hash
            mock_db.execute.assert_called_once()  # Delete chunks

    @pytest.mark.asyncio
    async def test_upsert_document_with_metadata(self):
        """Test that metadata parameter is accepted (even if not used yet)."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/document.txt"
        content = "Content"
        metadata = {"author": "test", "tags": ["doc", "test"]}

        with (
            patch("app.services.document_service.get_document_by_file_path") as mock_get_doc,
            patch("app.services.document_service.Document") as mock_document_class,
        ):
            mock_get_doc.return_value = None
            mock_document = Mock()
            mock_document.id = 999
            mock_document_class.return_value = mock_document

            result = await upsert_document(mock_db, file_path, content, metadata)

            assert result == 999
            # Metadata should not cause errors even though not used yet


class TestGetDocumentByFilePath:
    """Test the get_document_by_file_path function."""

    @pytest.mark.asyncio
    async def test_get_document_by_file_path_found(self):
        """Test retrieving an existing document."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/document.txt"
        mock_document = Mock()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        result = await get_document_by_file_path(mock_db, file_path)

        assert result == mock_document
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_file_path_not_found(self):
        """Test retrieving a non-existent document."""
        mock_db = AsyncMock(spec=AsyncSession)
        file_path = "/test/nonexistent.txt"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_document_by_file_path(mock_db, file_path)

        assert result is None


class TestCreateDocumentChunks:
    """Test the create_document_chunks function."""

    def test_create_document_chunks_success(self):
        """Test successful creation of document chunks."""
        embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        text = ["Chunk 1", "Chunk 2", "Chunk 3"]
        document_id = 123

        with patch("app.services.document_service.DocumentChunk") as mock_chunk_class:
            mock_chunks = [Mock(), Mock(), Mock()]
            mock_chunk_class.side_effect = mock_chunks

            result = create_document_chunks(embeddings, text, document_id)

            assert len(result) == 3
            assert result == mock_chunks

            # Verify each chunk was created with correct parameters
            for i, (mock_call, expected_text, expected_embedding) in enumerate(
                zip(mock_chunk_class.call_args_list, text, embeddings, strict=True)
            ):
                assert mock_call.kwargs["document_id"] == document_id
                assert mock_call.kwargs["content"] == expected_text
                assert mock_call.kwargs["embedding"] == expected_embedding
                assert mock_call.kwargs["chunk_index"] == i

    def test_create_document_chunks_mismatched_lengths(self):
        """Test error when embeddings and text lengths don't match."""
        embeddings = [[0.1, 0.2], [0.3, 0.4]]  # 2 embeddings
        text = ["Chunk 1", "Chunk 2", "Chunk 3"]  # 3 text chunks
        document_id = 123

        with pytest.raises(ValueError) as exc_info:
            create_document_chunks(embeddings, text, document_id)

        assert "Number of embeddings must match number of text chunks" in str(exc_info.value)

    def test_create_document_chunks_empty_lists(self):
        """Test with empty embeddings and text lists."""
        embeddings = []
        text = []
        document_id = 123

        result = create_document_chunks(embeddings, text, document_id)

        assert result == []


class TestUpsertDocumentChunks:
    """Test the upsert_document_chunks function."""

    @pytest.mark.asyncio
    async def test_upsert_document_chunks_success(self):
        """Test successful upserting of document chunks."""
        mock_db = AsyncMock(spec=AsyncSession)
        document_id = 123

        # Create mock chunks with IDs
        mock_chunks = []
        for i in range(3):
            chunk = Mock()
            chunk.id = i + 1
            mock_chunks.append(chunk)

        result = await upsert_document_chunks(mock_db, document_id, mock_chunks)

        assert result == [1, 2, 3]

        # Verify all chunks were added and document_id was set
        for chunk in mock_chunks:
            assert chunk.document_id == document_id

        assert mock_db.add.call_count == 3
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_document_chunks_empty_list(self):
        """Test upserting with empty chunks list."""
        mock_db = AsyncMock(spec=AsyncSession)
        document_id = 123
        chunks = []

        result = await upsert_document_chunks(mock_db, document_id, chunks)

        assert result == []
        mock_db.add.assert_not_called()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_document_chunks_sets_document_id(self):
        """Test that document_id is set on all chunks."""
        mock_db = AsyncMock(spec=AsyncSession)
        document_id = 456

        # Create chunks with different document_ids
        mock_chunks = []
        for i in range(2):
            chunk = Mock()
            chunk.id = i + 1
            chunk.document_id = 999  # Wrong document_id
            mock_chunks.append(chunk)

        await upsert_document_chunks(mock_db, document_id, mock_chunks)

        # Verify document_id was corrected on all chunks
        for chunk in mock_chunks:
            assert chunk.document_id == document_id
