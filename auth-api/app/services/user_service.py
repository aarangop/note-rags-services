"""
User service layer for authentication operations.
Create: auth-api/app/services/user_service.py
"""

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import Depends
from note_rags_db.schemas import RefreshToken, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.auth import UserRegisterRequest
from app.utils.password import generate_reset_token, hash_password, verify_password

logger = structlog.get_logger(__name__)


class UserService:
    """Service layer for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserRegisterRequest) -> User:
        """
        Create a new user account.

        Args:
            user_data: User registration data

        Returns:
            Created user object

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash the password
        hashed_password = hash_password(user_data.password)

        # Create user object
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False,  # Email verification not implemented yet
        )

        # Save to database
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info("Created new user", user_id=str(user.id), email=user.email)
        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by email
        user = await self.get_user_by_email(email)
        if not user:
            logger.warning("Authentication failed: user not found", email=email)
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning("Authentication failed: user inactive", email=email)
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning("Authentication failed: invalid password", email=email)
            return None

        # Update last login time
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()

        logger.info("User authenticated successfully", user_id=str(user.id), email=email)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> bool:
        """
        Change user's password.

        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully, False otherwise
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning("Password change failed: invalid current password", user_id=str(user_id))
            return False

        # Hash and update new password
        user.hashed_password = hash_password(new_password)
        await self.db.commit()

        logger.info("Password changed successfully", user_id=str(user_id))
        return True

    async def initiate_password_reset(self, email: str) -> str | None:
        """
        Initiate password reset process.

        Args:
            email: User's email

        Returns:
            Reset token if user found, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            # Don't reveal whether email exists for security
            logger.info("Password reset requested for non-existent email", email=email)
            return None

        # Generate reset token
        reset_token = generate_reset_token()
        reset_expires = datetime.now(UTC) + timedelta(hours=1)  # 1 hour expiry

        # Update user with reset token
        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        await self.db.commit()

        logger.info("Password reset token generated", user_id=str(user.id), email=email)
        return reset_token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password to set

        Returns:
            True if password reset successfully, False otherwise
        """
        # Find user by reset token
        result = await self.db.execute(select(User).where(User.password_reset_token == token))
        user = result.scalar_one_or_none()

        if not user or not user.is_password_reset_valid:
            logger.warning(
                "Password reset failed: invalid or expired token", token=token[:8] + "..."
            )
            return False

        # Update password and clear reset token
        user.hashed_password = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        await self.db.commit()

        logger.info("Password reset successfully", user_id=str(user.id))
        return True


class RefreshTokenService:
    """Service layer for refresh token operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_refresh_token(
        self, user_id: uuid.UUID, expires_in_days: int = 30
    ) -> RefreshToken:
        """Create a new refresh token for user."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=generate_reset_token(),  # Reuse secure token generator
            expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
        )

        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)

        logger.info("Created refresh token", user_id=str(user_id), token_id=str(refresh_token.id))
        return refresh_token

    async def get_valid_refresh_token(self, token_hash: str) -> RefreshToken | None:
        """Get valid refresh token by hash."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()

        if token:
            token.revoke()
            await self.db.commit()
            logger.info("Revoked refresh token", token_id=str(token.id))
            return True

        return False

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False)
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.revoke()

        await self.db.commit()

        logger.info("Revoked all refresh tokens for user", user_id=str(user_id), count=len(tokens))
        return len(tokens)


def get_user_service(db: AsyncSession = Depends(get_db)):
    return UserService(db)


def get_refresh_token_service(db: AsyncSession = Depends(get_db)):
    return RefreshTokenService(db)
