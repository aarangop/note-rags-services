"""User models for the Notes API."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response model for user information."""

    id: uuid.UUID
    cognito_user_id: str
    email: str
    username: str | None
    full_name: str | None
    is_active: bool
    is_verified: bool
    is_profile_complete: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Request model for updating user profile."""

    email: str | None = None
    username: str | None = None
    full_name: str | None = None


class UserRegistrationRequest(BaseModel):
    """Request model for user registration with profile data."""

    email: str
    username: str | None = None
    full_name: str | None = None
