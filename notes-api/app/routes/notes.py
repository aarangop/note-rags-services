from fastapi import APIRouter, Depends

from app.models.note import NoteCreate, NoteUpdate
from app.repositories.notes_repository import NotesRepository, get_notes_repository

router = APIRouter(tags=["notes"])


@router.get("/{id}")
async def get_note_by_id(id: int, repository: NotesRepository = Depends(get_notes_repository)):
    note = await repository.find_by_id(id)
    if note:
        return note
    return None


@router.post("/")
async def create_new_note(
    note: NoteCreate, repository: NotesRepository = Depends(get_notes_repository)
):
    new_note = await repository.create(note)
    return new_note


@router.put("/{id}")
async def update_note(
    id: int, note: NoteUpdate, repository: NotesRepository = Depends(get_notes_repository)
):
    updated_note = await repository.save(id, note)
    return updated_note


@router.delete("/{id}")
async def delete_note(id: int, repository: NotesRepository = Depends(get_notes_repository)):
    success = await repository.delete(id)
    return {"success": success}
