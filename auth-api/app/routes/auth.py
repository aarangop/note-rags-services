"""
Authentication API routes.
Create: auth-api/app/routes/auth.py
"""

import structlog
from auth_lib.jwt_service import JWTService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.models.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PublicKeyResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.jwt_service import get_jwt_service
from app.services.user_service import (
    RefreshTokenService,
    UserService,
    get_refresh_token_service,
    get_user_service,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# Helper function to get current user from token
async def get_current_user(
    token=Depends(security),
    user_service: UserService = Depends(get_user_service),
    jwt: JWTService = Depends(get_jwt_service),
):
    """Get current user from JWT token."""
    try:
        user_id = jwt.get_user_id_from_token(token.credentials)
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user

    except Exception as e:
        logger.warning("Token validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from e


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegisterRequest, user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user account.

    - **email**: Valid email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, number)
    - **full_name**: Optional full name
    """
    try:
        user = await user_service.create_user(user_data)

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )

    except ValueError as e:
        logger.warning("Registration failed", error=str(e), email=user_data.email)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Registration error", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed"
        ) from e


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLoginRequest,
    user_service: UserService = Depends(get_user_service),
    jwt_service: JWTService = Depends(get_jwt_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access token (15 min) and refresh token (30 days).
    """
    try:
        # Authenticate user
        user = await user_service.authenticate_user(credentials.email, credentials.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
            )

        # Create tokens
        access_token = jwt_service.create_access_token(user.id, user.email)
        refresh_token_obj = await refresh_token_service.create_refresh_token(user.id)

        logger.info("User logged in successfully", user_id=str(user.id), email=user.email)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_obj.token_hash,
            expires_in=jwt_service.access_token_expire_minutes * 60,  # Convert to seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", error=str(e), email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        ) from e


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    user_service: UserService = Depends(get_user_service),
    jwt_service: JWTService = Depends(get_jwt_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token.
    """
    try:
        # Validate refresh token
        refresh_token_obj = await refresh_token_service.get_valid_refresh_token(
            refresh_data.refresh_token
        )

        if not refresh_token_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
            )

        # Get user
        user = await user_service.get_user_by_id(refresh_token_obj.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
            )

        # Create new access token
        access_token = jwt_service.create_access_token(user.id, user.email)

        logger.info("Token refreshed", user_id=str(user.id))

        return AccessTokenResponse(
            access_token=access_token, expires_in=jwt_service.access_token_expire_minutes * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed"
        ) from e


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: TokenRefreshRequest,
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
):
    """
    Logout user by revoking refresh token.

    - **refresh_token**: Refresh token to revoke
    """
    try:
        success = await refresh_token_service.revoke_refresh_token(refresh_data.refresh_token)

        if success:
            logger.info("User logged out", refresh_token=refresh_data.refresh_token[:8] + "...")

        return MessageResponse(message="Logged out successfully", success=success)

    except Exception as e:
        logger.error("Logout error", error=str(e))
        # Don't raise error - logout should always succeed from user perspective
        return MessageResponse(message="Logged out successfully", success=True)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """
    Get current user information.

    Requires valid access token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Change user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password to set

    Requires valid access token.
    """
    try:
        success = await user_service.change_password(
            current_user.id, password_data.current_password, password_data.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password"
            )

        logger.info("Password changed", user_id=str(current_user.id))

        return MessageResponse(message="Password changed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change error", error=str(e), user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password change failed"
        ) from e


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    reset_data: PasswordResetRequest, user_service: UserService = Depends(get_user_service)
):
    """
    Initiate password reset process.

    - **email**: Email address to send reset link to

    Always returns success for security (doesn't reveal if email exists).
    """
    try:
        reset_token = await user_service.initiate_password_reset(reset_data.email)

        # TODO: Send email with reset_token
        # For now, we'll just log it (remove in production!)
        if reset_token:
            logger.info(
                "Password reset token generated",
                email=reset_data.email,
                token=reset_token[:8] + "...",
            )

        # Always return success for security
        return MessageResponse(message="If that email exists, a reset link has been sent")

    except Exception as e:
        logger.error("Password reset error", error=str(e), email=reset_data.email)
        # Still return success for security
        return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: PasswordResetConfirmRequest, user_service: UserService = Depends(get_user_service)
):
    """
    Reset password using reset token.

    - **token**: Password reset token from email
    - **new_password**: New password to set
    """
    try:
        success = await user_service.reset_password(reset_data.token, reset_data.new_password)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
            )

        logger.info("Password reset completed", token=reset_data.token[:8] + "...")

        return MessageResponse(message="Password reset successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password reset completion error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password reset failed"
        ) from e


@router.get("/public-key", response_model=PublicKeyResponse)
async def get_public_key(jwt_service: JWTService = Depends(get_jwt_service)):
    """
    Get RSA public key for JWT validation.

    Other microservices use this endpoint to get the public key
    for validating JWT tokens.
    """
    try:
        public_key = jwt_service.public_key

        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Public key not available",
            )

        return PublicKeyResponse(public_key=public_key, algorithm="RS256")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Public key retrieval error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve public key",
        ) from e
