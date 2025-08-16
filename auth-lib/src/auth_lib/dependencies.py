import json

import httpx
import jwt
from auth_lib.config import AuthSettings, get_auth_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from note_rags_db import get_async_db_session
from note_rags_db.schemas.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_cognito_public_keys = None

security = HTTPBearer()


class AuthenticationError(Exception):
    pass


class FailedToFetchPublicKeysError(AuthenticationError):
    pass


async def get_cognito_public_keys(jwks_url: str):
    """Fetch and cache Cognito public keys for JWT verification."""
    global _cognito_public_keys

    if _cognito_public_keys is None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()
                _cognito_public_keys = jwks
            except httpx.RequestError as e:
                raise FailedToFetchPublicKeysError() from e

    return _cognito_public_keys


async def verify_jwt_token(
    auth_settings: AuthSettings = Depends(get_auth_settings),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    try:
        # Get the token header to extract the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            raise AuthenticationError("Token missing key ID")

        # Get auth server public keys
        jwks = await get_cognito_public_keys(auth_settings.jwks_url)

        # Find the matching public key
        public_key = None

        for key in jwks["keys"]:
            if key["kid"] == kid:
                # Ensure we get public key component
                jwk_dict = json.dumps(key)
                public_key = jwt.PyJWK.from_json(jwk_dict)
                break

        if not public_key:
            raise AuthenticationError("Unable to find matching public key")

        # Verify and decode token
        options = {
            "verify_exp": auth_settings.jwt_verify_expiration,
            "verify_aud": auth_settings.jwt_verify_audience,
            "verify_iss": auth_settings.jwt_verify_issuer,
        }
        payload = jwt.decode(
            token,
            public_key,
            algorithms=auth_settings.jwt_algorithm,
            issuer=auth_settings.jwt_issuer,
            options=options,
        )
        return payload

    except jwt.ExpiredSignatureError as e:
        raise e
    except jwt.InvalidTokenError as e:
        raise e
    except Exception as e:
        raise AuthenticationError(e) from e


async def get_current_user(
    token_payload: dict = Depends(verify_jwt_token),
    db: AsyncSession = Depends(get_async_db_session),
) -> User:
    """Extract user information from JWT and enrich with database data."""

    # Extract basic user info from token
    cognito_user_id = token_payload.get("sub")
    token_use = token_payload.get("token_use", "access")

    if not cognito_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required information"
        )

    # Verify this is an access token
    if token_use != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Look up user in database by cognito_user_id
    stmt = select(User).where(User.cognito_user_id == cognito_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # If user doesn't exist, create a new user record
    if not user:
        # Extract additional user info from token
        full_name = token_payload.get("name") or token_payload.get(
            "given_name", ""
        ) + " " + token_payload.get("family_name", "")
        if full_name.strip() == " ":
            full_name = None

        # Create new user
        user = User(
            cognito_user_id=cognito_user_id,
            email="",
            full_name=full_name.strip() if full_name else None,
            is_active=True,
            is_verified=True,  # Cognito handles verification
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )

    return user
