import datetime
from enum import Enum
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from note_rags_db.db import Base


class DocumentType(Enum):
    NOTE = "note"
    PDF = "pdf"


class Document(Base):
    """
    SQLAlchemy ORM model representing documents in the database.

    This class defines the document schema with fields for tracking document content,
    file location, creation/update timestamps, and content hash for change detection.

    Attributes:
        id (int): Primary key for the document.
        file_path (str): Path to the document file, indexed and unique.
        content (str): Full text content of the document.
        created_at (datetime): Timestamp when the document was first created.
        updated_at (datetime): Timestamp of the last update to the document.
        content_hash (str): SHA hash of the document content for change detection.
        chunks (list): Related document chunks extracted from this document.
    """

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    file_path: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(default=func.now(), onupdate=func.now())
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    document_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DocumentType.NOTE.value, index=True
    )
    document_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationship
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")


class DocumentChunk(Base):
    """
    Represents a chunk of a document in the system.

    A document chunk is a segment of a document that has been processed for embedding and retrieval.
    Each chunk contains a portion of the document's content and its corresponding vector embedding.

    Attributes:
        id (int): Primary key for the document chunk.
        document_id (int): Foreign key referencing the parent document.
        content (str): The text content of this specific chunk.
        chunk_index (int): The sequential index of this chunk within its parent document.
        embedding (list[float]): Vector representation of the chunk content, dimensionality of 1536.
        document (Document): Relationship to the parent document.
    """

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    content: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))

    # Relationship
    document: Mapped["Document"] = relationship(back_populates="chunks")
