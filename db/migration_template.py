"""Add content_hash column with data population

Revision ID: {revision_id}
Revises: 0e5a232be495
Create Date: {date}

"""

import hashlib
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "{revision_id}"
down_revision: str | Sequence[str] | None = "0e5a232be495"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the content_hash column as nullable first
    op.add_column("documents", sa.Column("content_hash", sa.String(length=64), nullable=True))

    # Populate content_hash for existing records
    connection = op.get_bind()

    # Get all documents without content_hash
    result = connection.execute(
        text("SELECT id, content FROM documents WHERE content_hash IS NULL")
    )

    # Update each document with its content hash
    for row in result:
        content = row.content
        if content:
            # Calculate SHA-256 hash of the content
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            connection.execute(
                text("UPDATE documents SET content_hash = :hash WHERE id = :doc_id"),
                {"hash": content_hash, "doc_id": row.id},
            )

    # Now make the column non-nullable
    op.alter_column("documents", "content_hash", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("documents", "content_hash")
