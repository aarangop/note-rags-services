from datetime import datetime

from app.db import get_db
from app.models.note import Note, NoteCreate, NoteUpdate
from app.repositories.notes_repository import NotesRepository, get_notes_repository
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


class NotesService:
    def __init__(self, db: AsyncSession, repository: NotesRepository):
        self.db = db
        self.repository = repository

    def generate_unique_title(self, base_title: str | None = "Untitled Note") -> str:
        # Find the highest number for "Untitled X" pattern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_title} {timestamp}"

    async def create(self, note: NoteCreate) -> Note:
        title = note.title if note.title else self.generate_unique_title()
        note.title = title
        return await self.repository.create(note)

    async def save(self, id: int, note: NoteUpdate) -> Note | None:
        return await self.repository.save(id, note)

    async def delete(self, id: int) -> bool:
        return await self.repository.delete(id)


def get_notes_service(
    db: AsyncSession = Depends(get_db), repository: NotesRepository = Depends(get_notes_repository)
):
    return NotesService(db, repository)
