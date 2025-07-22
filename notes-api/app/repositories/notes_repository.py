from fastapi import Depends
from note_rags_db.schemas import Document
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.note import Note, NoteCreate, NoteUpdate


class NoteNotFoundError(Exception):
    """Exception raised when a note is not found in the database."""


class NotesRepository:
    """
    Repository class for managing note-related database operations.

    This class provides methods to create, read, update, and delete notes
    in the database using SQLAlchemy's async session.

    Attributes:
        db (AsyncSession): SQLAlchemy async database session used for all database operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, note: NoteCreate) -> Note:
        """
        Creates a new note in the database.

        Args:
            note (NoteCreate): The note data to create in the database

        Returns:
            NoteResponse: The created note with all fields populated, including database-generated fields

        Raises:
            Exception: If any database error occurs during the creation process
        """
        try:
            document = note.to_db_model()
            self.db.add(document)
            await self.db.refresh(document)
            await self.db.commit()

            # Convert created Document to NoteResponse using the class method
            return Note.from_document(document)
        except Exception:
            await self.db.rollback()
            raise

    async def save(self, note_id: int, note: NoteUpdate) -> Note | None:
        """
        Update an existing note in the database with non-None values from the provided update.

        Args:
            note_id (int): The ID of the note to update.
            note (NoteUpdate): The update data containing new values for the note.

        Returns:
            NoteResponse | None: The updated note as a NoteResponse object if found and updated successfully,
                                 or None if the note doesn't exist or an error occurred during the update.

        Raises:
            No exceptions are raised directly as they are caught internally and None is returned.
        """
        try:
            document = await self.db.get(Document, note_id)
            if document is None:
                raise NoteNotFoundError(f"Note with id {note_id} not found")

            # Update document fields with non-None values from the update
            if note.title is not None:
                document.title = note.title
            if note.content is not None:
                document.content = note.content
            if note.metadata is not None:
                document.document_metadata = note.metadata

            await self.db.commit()
            await self.db.refresh(document)

            # Convert updated Document to NoteResponse using the class method
            return Note.from_document(document)
        except NoteNotFoundError:
            # Re-raise NoteNotFoundError so it can be handled by the route
            raise
        except Exception:
            await self.db.rollback()
            return None

    async def delete(self, id: int) -> bool:
        """
        Delete a note by ID.

        Args:
            id (int): The ID of the note to delete.

        Returns:
            bool: True if the note was successfully deleted, False if the note was not found or if an error occurred during deletion.

        Raises:
            None: Exceptions are caught and handled internally, returning False on any exception.
        """
        try:
            document = await self.db.get(Document, id)
            if document is None:
                return False

            await self.db.delete(document)
            await self.db.commit()
            return True
        except Exception:
            await self.db.rollback()
            return False

    async def find_by_id(self, note_id: int) -> Note | None:
        """
        Retrieve a note by its ID from the database.

        This method fetches a document with the specified ID and converts it to a NoteResponse object.
        If no document is found with the given ID, returns None.

        Args:
            note_id (int): The unique identifier of the note to retrieve.

        Returns:
            NoteResponse | None: A NoteResponse object containing the note data if found, None otherwise.

        Raises:
            Exception: If there's an error accessing the database or processing the document.
        """
        try:
            document = await self.db.get(Document, note_id)
            if document is None:
                raise NoteNotFoundError(f"Note with id {note_id} not found")

            # Convert Document to NoteResponse using the class method
            return Note.from_document(document)
        except Exception:
            # For read operations, we don't need rollback, but we should re-raise the exception
            # so the caller can handle it appropriately (e.g., return 500 error)
            raise

    async def find_by_title(self, title: str) -> Note | None:
        """
        Retrieve a note by its title from the database.

        Args:
            title (str): The title of the note to retrieve.

        Returns:
            NoteResponse | None: A NoteResponse object containing the note data if found, None otherwise.

        Raises:
            Exception: If there's an error accessing the database or processing the document.
        """
        try:
            query = select(Document).where(Document.title == title)
            result = await self.db.execute(query)
            document = result.scalar_one_or_none()

            if document is None:
                raise NoteNotFoundError(f"Note with title '{title}' not found")

            return Note.from_document(document)
        except Exception:
            # For read operations, we don't need rollback
            raise


def get_notes_repository(db: AsyncSession = Depends(get_db)):
    return NotesRepository(db)
