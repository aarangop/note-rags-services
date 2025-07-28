from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.note import Note, NoteCreate, NotesPage, NoteUpdate
from app.repositories.notes_repository import (
    NoteNotFoundError,
    NotesRepository,
    get_notes_repository,
)

router = APIRouter(tags=["notes"])


class NoteNotFoundHTTPException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)


@router.get("/", response_model=NotesPage)
async def get_notes(
    repository: NotesRepository = Depends(get_notes_repository),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    offset = (page - 1) * size
    notes = await repository.find_all(limit=size, offset=offset)
    total = await repository.count()

    return NotesPage(
        items=notes, page=page, size=size, total=total, pages=(total + size - 1) // size
    )


@router.get("/{id}", response_model=Note)
async def get_note_by_id(id: int, repository: NotesRepository = Depends(get_notes_repository)):
    try:
        note = await repository.find_by_id(id)
        return note
    except NoteNotFoundError as e:
        raise NoteNotFoundHTTPException(str(e)) from e


@router.post("/", response_model=Note)
async def create_new_note(
    note: NoteCreate, repository: NotesRepository = Depends(get_notes_repository)
):
    new_note = await repository.create(note)
    return new_note


@router.put("/{id}", response_model=Note)
async def update_note(
    id: int, note: NoteUpdate, repository: NotesRepository = Depends(get_notes_repository)
):
    try:
        updated_note = await repository.save(id, note)
        return updated_note
    except NoteNotFoundError as e:
        raise NoteNotFoundHTTPException(str(e)) from e


@router.delete("/{id}")
async def delete_note(id: int, repository: NotesRepository = Depends(get_notes_repository)):
    success = await repository.delete(id)
    return {"success": success}
