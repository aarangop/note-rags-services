"""
Pydantic models for authentication API.
Create: auth-api/app/models/auth.py
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Request model for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    full_name: str | None = Field(None, max_length=255, description="User's full name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v


class UserLoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenRefreshRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""

    email: EmailStr = Field(..., description="User's email address")


class PasswordResetConfirmRequest(BaseModel):
    """Request model for password reset confirmation."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v


class ChangePasswordRequest(BaseModel):
    """Request model for password change."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        return v


# Response Models


class UserResponse(BaseModel):
    """Response model for user information."""

    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: datetime | None


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AccessTokenResponse(BaseModel):
    """Response model for access token only (refresh endpoint)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True


class PublicKeyResponse(BaseModel):
    """Response model for public key endpoint."""

    public_key: str
    algorithm: str = "RS256"


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None
    success: bool = False
