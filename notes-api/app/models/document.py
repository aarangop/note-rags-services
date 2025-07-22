import hashlib
from datetime import datetime

from note_rags_db.schemas import Document, DocumentType
from pydantic import BaseModel, ConfigDict, Field


class BaseDocument(BaseModel):
    file_path: str
    title: str
    content: str
    document_type: DocumentType
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = {}

    def to_db_model(self) -> Document:
        return Document(
            file_path=self.file_path,
            title=self.title,
            content=self.content,
            updated_at=self.updated_at,
            created_at=self.created_at,
            content_hash=hashlib.sha256(self.content.encode("utf-8")).hexdigest(),
        )


class DocumentCreate(BaseDocument):
    pass


class DocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict | None = {}
    updated_at: datetime = Field(default_factory=datetime.now)


class DocumentResponse(BaseDocument):
    id: int
    file_path: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_db_model(cls, document: Document) -> "DocumentResponse":
        return cls.model_validate(document)
