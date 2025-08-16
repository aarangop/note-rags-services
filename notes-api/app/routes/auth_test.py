"""Authentication test routes for the Notes API."""

from auth_lib.dependencies import get_current_user
from fastapi import APIRouter, Depends
from note_rags_db.schemas.user import User

from app.models.user import UserResponse

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
