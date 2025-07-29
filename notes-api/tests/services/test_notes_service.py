from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.note import Note, NoteCreate, NoteUpdate
from app.repositories.notes_repository import NotesRepository
from app.services.notes_service import NotesService
from sqlalchemy.ext.asyncio import AsyncSession


class TestNotesService:
    @pytest.fixture
    def mock_db(self):
        """Fixture for mocked database session."""
        return Mock(spec=AsyncSession)

    @pytest.fixture
    def mock_repository(self):
        """Fixture for mocked notes repository."""
        repository = Mock(spec=NotesRepository)
        repository.create = AsyncMock()
        repository.save = AsyncMock()
        repository.delete = AsyncMock()
        return repository

    @pytest.fixture
    def notes_service(self, mock_db, mock_repository):
        """Fixture for NotesService with mocked dependencies."""
        return NotesService(mock_db, mock_repository)

    @pytest.fixture
    def sample_note_create(self):
        """Fixture for sample NoteCreate data."""
        return NoteCreate(
            file_path="/test/path",
            title="Test Note",
            content="Test content",
            metadata={"key": "value"},
        )

    @pytest.fixture
    def sample_note_create_no_title(self):
        """Fixture for sample NoteCreate data without title."""
        return NoteCreate(
            file_path="/test/path",
            title="",
            content="Test content",
            metadata={"key": "value"},
        )

    @pytest.fixture
    def sample_note(self):
        """Fixture for sample Note data."""
        return Note(
            id=1,
            file_path="/test/path",
            title="Test Note",
            content="Test content",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"key": "value"},
        )

    @pytest.fixture
    def sample_note_update(self):
        """Fixture for sample NoteUpdate data."""
        return NoteUpdate(
            title="Updated Title", content="Updated content", metadata={"updated": "value"}
        )

    def test_init(self, mock_db, mock_repository):
        """Test NotesService initialization."""
        service = NotesService(mock_db, mock_repository)
        assert service.db == mock_db
        assert service.repository == mock_repository

    def test_generate_unique_title_default(self, notes_service):
        """Test generate_unique_title with default base title."""
        with patch("app.services.notes_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250729_143000"

            title = notes_service.generate_unique_title()

            assert title == "Untitled Note 20250729_143000"
            mock_datetime.now.assert_called_once()
            mock_datetime.now.return_value.strftime.assert_called_once_with("%Y%m%d_%H%M%S")

    def test_generate_unique_title_custom_base(self, notes_service):
        """Test generate_unique_title with custom base title."""
        with patch("app.services.notes_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250729_143000"

            title = notes_service.generate_unique_title("My Note")

            assert title == "My Note 20250729_143000"
            mock_datetime.now.assert_called_once()
            mock_datetime.now.return_value.strftime.assert_called_once_with("%Y%m%d_%H%M%S")

    def test_generate_unique_title_none_base(self, notes_service):
        """Test generate_unique_title with None as base title."""
        with patch("app.services.notes_service.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20250729_143000"

            title = notes_service.generate_unique_title(None)

            assert title == "None 20250729_143000"
            mock_datetime.now.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_title(
        self, notes_service, mock_repository, sample_note_create, sample_note
    ):
        """Test create method with provided title."""
        mock_repository.create.return_value = sample_note

        result = await notes_service.create(sample_note_create)

        assert result == sample_note
        assert sample_note_create.title == "Test Note"  # Title should remain unchanged
        mock_repository.create.assert_called_once_with(sample_note_create)

    @pytest.mark.asyncio
    async def test_create_without_title(
        self, notes_service, mock_repository, sample_note_create_no_title, sample_note
    ):
        """Test create method without provided title (should generate unique title)."""
        mock_repository.create.return_value = sample_note

        with patch.object(
            notes_service, "generate_unique_title", return_value="Generated Title 20250729_143000"
        ) as mock_generate:
            result = await notes_service.create(sample_note_create_no_title)

            assert result == sample_note
            assert sample_note_create_no_title.title == "Generated Title 20250729_143000"
            mock_generate.assert_called_once()
            mock_repository.create.assert_called_once_with(sample_note_create_no_title)

    @pytest.mark.asyncio
    async def test_create_with_empty_title(
        self, notes_service, mock_repository, sample_note, sample_note_create
    ):
        """Test create method with empty string title (should generate unique title)."""
        sample_note_create.title = ""
        mock_repository.create.return_value = sample_note

        with patch.object(
            notes_service, "generate_unique_title", return_value="Generated Title 20250729_143000"
        ) as mock_generate:
            result = await notes_service.create(sample_note_create)

            assert result == sample_note
            assert sample_note_create.title == "Generated Title 20250729_143000"
            mock_generate.assert_called_once()
            mock_repository.create.assert_called_once_with(sample_note_create)

    @pytest.mark.asyncio
    async def test_save_success(
        self, notes_service, mock_repository, sample_note_update, sample_note
    ):
        """Test save method with successful update."""
        mock_repository.save.return_value = sample_note

        result = await notes_service.save(1, sample_note_update)

        assert result == sample_note
        mock_repository.save.assert_called_once_with(1, sample_note_update)

    @pytest.mark.asyncio
    async def test_save_not_found(self, notes_service, mock_repository, sample_note_update):
        """Test save method when note is not found."""
        mock_repository.save.return_value = None

        result = await notes_service.save(999, sample_note_update)

        assert result is None
        mock_repository.save.assert_called_once_with(999, sample_note_update)

    @pytest.mark.asyncio
    async def test_delete_success(self, notes_service, mock_repository):
        """Test delete method with successful deletion."""
        mock_repository.delete.return_value = True

        result = await notes_service.delete(1)

        assert result is True
        mock_repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_not_found(self, notes_service, mock_repository):
        """Test delete method when note is not found."""
        mock_repository.delete.return_value = False

        result = await notes_service.delete(999)

        assert result is False
        mock_repository.delete.assert_called_once_with(999)

    @pytest.mark.asyncio
    async def test_create_repository_exception(
        self, notes_service, mock_repository, sample_note_create
    ):
        """Test create method when repository raises an exception."""
        mock_repository.create.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await notes_service.create(sample_note_create)

        mock_repository.create.assert_called_once_with(sample_note_create)

    @pytest.mark.asyncio
    async def test_save_repository_exception(
        self, notes_service, mock_repository, sample_note_update
    ):
        """Test save method when repository raises an exception."""
        mock_repository.save.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await notes_service.save(1, sample_note_update)

        mock_repository.save.assert_called_once_with(1, sample_note_update)

    @pytest.mark.asyncio
    async def test_delete_repository_exception(self, notes_service, mock_repository):
        """Test delete method when repository raises an exception."""
        mock_repository.delete.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await notes_service.delete(1)

        mock_repository.delete.assert_called_once_with(1)
