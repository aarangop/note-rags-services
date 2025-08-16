"""Authentication test routes for the Notes API."""

from auth_lib.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from note_rags_db import get_async_db_session
from note_rags_db.schemas.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import ProfileUpdateRequest, UserRegistrationRequest, UserResponse

router = APIRouter(tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    This endpoint demonstrates the Cognito JWT authentication integration.
    It validates the JWT token and returns the user information from the database.

    - **Authorization**: Bearer token required (Cognito JWT)
    - **Returns**: User information including Cognito ID, email, and profile data

    ## Usage
    1. Obtain a JWT token using the `scripts/get-cognito-token.py` script
    2. Include the token in the Authorization header: `Bearer <your-token>`
    3. Send a GET request to this endpoint

    The endpoint will:
    - Validate the JWT token against Cognito's JWKS
    - Look up the user in the database by cognito_user_id
    - Create a new user record if this is the first time accessing the API
    - Return the complete user information
    """
    return UserResponse.model_validate(current_user)


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information.

    This is an alias for the `/me` endpoint for profile-specific operations.

    - **Authorization**: Bearer token required (Cognito JWT)
    - **Returns**: Complete user profile information
    """
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session),
):
    """
    Update current user's profile information.

    Allows updating email, username, and full_name. Only provided fields will be updated.
    Automatically sets is_profile_complete to True when email is provided.

    - **Authorization**: Bearer token required (Cognito JWT)
    - **Body**: JSON with optional email, username, and/or full_name fields
    - **Returns**: Updated user profile information

    ## Validation Rules
    - Email must be unique across all users
    - Username must be unique across all users (if provided)
    - At least one field must be provided for update
    """
    # Check if there's anything to update
    update_data = profile_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be provided for update",
        )

    # Check email uniqueness if email is being updated
    if profile_data.email is not None and profile_data.email != current_user.email:
        stmt = select(User).where(User.email == profile_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email address is already in use"
            )

    # Check username uniqueness if username is being updated
    if profile_data.username is not None and profile_data.username != current_user.username:
        stmt = select(User).where(User.username == profile_data.username)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username is already in use"
            )

    # Update user fields
    if profile_data.email is not None:
        current_user.email = profile_data.email
        current_user.is_profile_complete = True  # Mark profile as complete when email is set

    if profile_data.username is not None:
        current_user.username = profile_data.username

    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    # Save changes
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/register", response_model=UserResponse)
async def register_user_with_profile(
    registration_data: UserRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session),
):
    """
    Complete user registration with profile information.

    This endpoint allows setting complete profile information in one call.
    Intended for use immediately after first authentication when user needs
    to complete their profile.

    - **Authorization**: Bearer token required (Cognito JWT)
    - **Body**: JSON with required email and optional username, full_name
    - **Returns**: Updated user profile information

    ## Usage Pattern
    1. User authenticates with Cognito (auto-creates minimal user record)
    2. Frontend calls this endpoint to complete registration with profile data
    3. User profile is marked as complete

    ## Validation Rules
    - Email is required and must be unique
    - Username must be unique if provided
    - Will update existing auto-created user record
    """
    # Check email uniqueness
    if registration_data.email != current_user.email:
        stmt = select(User).where(User.email == registration_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email address is already in use"
            )

    # Check username uniqueness if provided
    if registration_data.username and registration_data.username != current_user.username:
        stmt = select(User).where(User.username == registration_data.username)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username is already in use"
            )

    # Update user with registration data
    current_user.email = registration_data.email
    current_user.is_profile_complete = True

    if registration_data.username:
        current_user.username = registration_data.username

    if registration_data.full_name:
        current_user.full_name = registration_data.full_name

    # Save changes
    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)
