from pydantic import BaseModel, ConfigDict

from app.models.document import BaseDocument, DocumentType


class BaseNote(BaseDocument):
    document_type: DocumentType = DocumentType.NOTE
    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseNote):
    pass


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict | None = None


class Note(BaseNote):
    id: int

    @classmethod
    def from_document(cls, document) -> "Note":
        """
        Create a NoteResponse from a database Document object.

        Args:
            document: Database Document object with all the necessary fields

        Returns:
            NoteResponse: A new NoteResponse instance with data from the document
        """
        return cls(
            id=document.id,
            file_path=document.file_path,
            title=document.title,
            content=document.content,
            document_type=DocumentType.NOTE,
            created_at=document.created_at,
            updated_at=document.updated_at,
            metadata=document.document_metadata
            if hasattr(document, "document_metadata") and document.document_metadata
            else {},
        )
