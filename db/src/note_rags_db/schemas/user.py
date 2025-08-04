import datetime
import uuid

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from note_rags_db.db import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile information
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(default=func.now(), onupdate=func.now())
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    password_reset_expires: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    # Email verification
    verification_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_expires: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    @property
    def is_password_reset_valid(self) -> bool:
        """Check if password reset token is still valid."""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        return datetime.datetime.now() < self.password_reset_expires

    @property
    def is_verification_valid(self) -> bool:
        """Check if verification token is still valid."""
        if not self.verification_token or not self.verification_expires:
            return False
        return datetime.datetime.now() < self.verification_expires


class RefreshToken(Base):
    """Refresh token model for JWT token rotation."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )  # No FK constraint - auth service is independent

    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    # Track token usage
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    # Optional: track client info for security
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compatible

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_valid(self) -> bool:
        """Check if refresh token is still valid."""
        return not self.is_revoked and datetime.datetime.utcnow() < self.expires_at

    def revoke(self) -> None:
        """Revoke the refresh token."""
        self.is_revoked = True
        self.revoked_at = datetime.datetime.now()
