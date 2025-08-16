"""User models for the Notes API."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response model for user information."""
    
    id: uuid.UUID
    cognito_user_id: str
    email: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True