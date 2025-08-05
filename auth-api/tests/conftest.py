"""
Shared test fixtures and configuration.
"""

import os
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from note_rags_db import MockAsyncSession, MockDBConfig, create_mock_db_config
from note_rags_db.schemas import RefreshToken, User

# Set test environment variables before any imports
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_for_testing_only")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USERNAME", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("PRIVATE_KEY_PATH", "/tmp/test_private_key.pem")
os.environ.setdefault("PUBLIC_KEY_PATH", "/tmp/test_public_key.pem")


@pytest.fixture
def mock_user():
    """Mock user data."""
    return User(
        id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
        email="test@example.com",
        hashed_password="$2b$12$hashed_password_here",
        full_name="Test User",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
        last_login_at=None,
        password_reset_token=None,
        password_reset_expires=None,
    )


@pytest.fixture
def mock_inactive_user():
    """Mock inactive user data."""
    return User(
        id=uuid.UUID("87654321-4321-8765-2109-876543210987"),
        email="inactive@example.com",
        hashed_password="$2b$12$hashed_password_here",
        full_name="Inactive User",
        is_active=False,
        is_verified=False,
        created_at=datetime.now(UTC),
        last_login_at=None,
        password_reset_token=None,
        password_reset_expires=None,
    )


@pytest.fixture
def mock_refresh_token():
    """Mock refresh token data."""
    return RefreshToken(
        id=uuid.UUID("87654321-4321-8765-2109-876543210987"),
        user_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
        token_hash="mock_refresh_token_hash",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_revoked=False,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_expired_refresh_token():
    """Mock expired refresh token data."""
    return RefreshToken(
        id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        user_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
        token_hash="expired_refresh_token_hash",
        expires_at=datetime.now(UTC) - timedelta(days=1),  # Expired
        is_revoked=False,
        created_at=datetime.now(UTC) - timedelta(days=31),
    )


@pytest.fixture
def mock_revoked_refresh_token():
    """Mock revoked refresh token data."""
    return RefreshToken(
        id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        user_id=uuid.UUID("12345678-1234-5678-9012-123456789012"),
        token_hash="revoked_refresh_token_hash",
        expires_at=datetime.now(UTC) + timedelta(days=30),
        is_revoked=True,  # Revoked
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_jwt_service():
    """Mock JWT service."""
    jwt_service = MagicMock()
    jwt_service.create_access_token.return_value = "mock_access_token"
    jwt_service.access_token_expire_minutes = 15
    jwt_service.public_key = "-----BEGIN PUBLIC KEY-----\nMOCK_PUBLIC_KEY\n-----END PUBLIC KEY-----"
    jwt_service.get_user_id_from_token.return_value = uuid.UUID(
        "12345678-1234-5678-9012-123456789012"
    )
    return jwt_service


@pytest.fixture
def valid_user_payload():
    """Valid user registration payload."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def valid_login_payload():
    """Valid login payload."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
    }


@pytest.fixture
def invalid_password_payloads():
    """Various invalid password payloads for testing."""
    return [
        {
            "email": "test@example.com",
            "password": "short",  # Too short
            "full_name": "Test User",
        },
        {
            "email": "test@example.com",
            "password": "nouppercase123",  # No uppercase
            "full_name": "Test User",
        },
        {
            "email": "test@example.com",
            "password": "NOLOWERCASE123",  # No lowercase
            "full_name": "Test User",
        },
        {
            "email": "test@example.com",
            "password": "NoNumbers",  # No numbers
            "full_name": "Test User",
        },
    ]


@pytest.fixture
def invalid_email_payloads():
    """Various invalid email payloads for testing."""
    return [
        {
            "email": "invalid-email",  # No @ or domain
            "password": "TestPassword123",
            "full_name": "Test User",
        },
        {
            "email": "@example.com",  # No local part
            "password": "TestPassword123",
            "full_name": "Test User",
        },
        {
            "email": "test@",  # No domain
            "password": "TestPassword123",
            "full_name": "Test User",
        },
    ]


@pytest.fixture
def authorization_headers():
    """Mock authorization headers."""
    return {"Authorization": "Bearer valid_access_token"}


@pytest.fixture
def mock_db_session():
    """Mock database session using the db package utilities."""
    return MockAsyncSession()


@pytest.fixture
def mock_db_config():
    """Mock database config using the db package utilities."""
    return create_mock_db_config()
