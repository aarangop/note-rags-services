"""
Improved authentication tests that focus on API contracts rather than implementation details.

These tests are less brittle than the original mocking-heavy tests while still being practical to run.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from note_rags_db.testing import create_mock_async_session

# Set environment variables before importing anything
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_USERNAME"] = "test_user"
os.environ["DB_PASSWORD"] = "test_password"
os.environ["DB_NAME"] = "test_db"
os.environ["PRIVATE_KEY_PATH"] = "/tmp/test_private_key.pem"
os.environ["PUBLIC_KEY_PATH"] = "/tmp/test_public_key.pem"


@pytest.fixture
def mock_db():
    """Create a mock database session using note_rags_db mocking utilities."""
    session = create_mock_async_session()

    # Define a custom refresh handler for auth API objects
    def auth_refresh_handler(obj):
        """Custom refresh handler that sets UUID and datetime fields for auth objects."""
        import uuid
        from datetime import UTC, datetime

        if not hasattr(obj, "id") or obj.id is None:
            obj.id = uuid.uuid4()
        if not hasattr(obj, "created_at") or obj.created_at is None:
            obj.created_at = datetime.now(UTC)

    session.set_refresh_handler(auth_refresh_handler)
    return session


@pytest.fixture
def test_app(mock_db):
    """Create a test FastAPI app with minimal mocking."""
    app = FastAPI(title="Test Auth API")

    # Import and include the router
    from app.routes.auth import router

    app.include_router(router)

    # Override the database dependency to return our mock
    from app.db import get_db

    app.dependency_overrides[get_db] = lambda: mock_db

    yield app

    # Clean up the override after test
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


class TestAuth:
    """Improved auth tests focusing on API contracts and key behaviors."""

    def test_register_success_creates_user(self, client, mock_db):
        """Test that successful registration returns correct response format."""
        # Configure mock for the email lookup query (should return None - no existing user)
        mock_db.set_query_result("scalars_results", [])

        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User",
        }

        # Mock password hashing to avoid bcrypt issues in tests
        with patch("app.utils.password.hash_password", return_value="hashed_password"):
            response = client.post("/auth/register", json=user_data)

        # Test API contract
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data

        # Verify key database operations happened
        assert mock_db.added_objects  # User was added
        assert mock_db.committed  # Changes were committed

    def test_register_duplicate_email_fails(self, client, mock_db):
        """Test that duplicate email registration fails appropriately."""

        # Mock: email already exists
        existing_user = MagicMock()
        existing_user.email = "test@example.com"
        mock_db.set_query_result("scalars_results", [existing_user])

        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123",
            "full_name": "Test User",
        }

        # Mock password hashing to avoid bcrypt issues in tests
        with patch("app.utils.password.hash_password", return_value="hashed_password"):
            response = client.post("/auth/register", json=user_data)

        # Test error response contract
        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]

        # Verify no user was added to database
        assert not mock_db.added_objects

    def test_login_success_returns_tokens(self, client, mock_db):
        """Test that successful login returns both access and refresh tokens."""

        # Mock user exists and is active
        mock_user = MagicMock()
        mock_user.id = "12345678-1234-5678-9012-123456789012"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        # Use a properly formatted bcrypt hash (this is a real hash for "password")
        mock_user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWR8hnTQEiDVr0Qe"

        # Set up database mock to return the user for email lookup
        mock_db.set_query_result("scalars_results", [mock_user])

        # Mock password verification and JWT service
        with patch("app.services.user_service.verify_password", return_value=True):
            login_data = {"email": "test@example.com", "password": "TestPassword123"}
            response = client.post("/auth/login", json=login_data)

            # Test API contract
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["access_token"]  # Token should exist and not be empty
            assert "refresh_token" in data
            assert data["refresh_token"]  # Refresh token should exist and not be empty
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            assert data["expires_in"] > 0  # Should have a positive expiration time

            # Verify refresh token was created and saved
            assert mock_db.added_objects  # Refresh token added
            assert mock_db.committed  # Changes committed

    def test_login_invalid_credentials_fails(self, client, mock_db):
        """Test that invalid credentials are properly rejected."""

        # Mock user doesn't exist
        mock_db.set_query_result("scalars_results", [])

        login_data = {"email": "test@example.com", "password": "WrongPassword"}
        response = client.post("/auth/login", json=login_data)

        # Test error response contract
        assert response.status_code == 401
        data = response.json()
        assert "Invalid email or password" in data["detail"]

        # Verify no tokens were created
        assert not mock_db.added_objects

    def test_password_validation_enforced(self, client):
        """Test that password validation rules are enforced."""
        weak_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoNumbers",  # No numbers
        ]

        for weak_password in weak_passwords:
            user_data = {
                "email": "test@example.com",
                "password": weak_password,
                "full_name": "Test User",
            }

            response = client.post("/auth/register", json=user_data)

            # Should fail validation
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data

    def test_token_refresh_validates_token(self, client):
        """Test that token refresh validates the refresh token."""
        # Create a custom mock session for this complex test
        mock_db = create_mock_async_session()

        # Mock valid refresh token
        mock_token = MagicMock()
        mock_token.user_id = "12345678-1234-5678-9012-123456789012"
        mock_token.is_revoked = False

        # Mock user
        mock_user = MagicMock()
        mock_user.id = "12345678-1234-5678-9012-123456789012"
        mock_user.email = "test@example.com"
        mock_user.is_active = True

        # Set up database mock to return different results for different queries
        # Use a counter to track which query this is
        call_count = [0]
        original_execute = mock_db.execute

        async def multi_result_execute(statement, parameters=None):
            result = await original_execute(statement, parameters)
            call_count[0] += 1

            # First call returns the refresh token, second call returns the user
            if call_count[0] == 1:
                # Token lookup
                mock_db.set_query_result("scalars_results", [mock_token])
            else:
                # User lookup
                mock_db.set_query_result("scalars_results", [mock_user])

            return result

        mock_db.execute = multi_result_execute

        # Create test app with this specific mock
        app = FastAPI(title="Test Auth API")
        from app.routes.auth import router

        app.include_router(router)
        from app.db import get_db

        app.dependency_overrides[get_db] = lambda: mock_db

        client_instance = TestClient(app)

        # Mock JWT service
        with patch("app.services.jwt_service.get_jwt_service") as mock_jwt_service:
            mock_jwt = MagicMock()
            mock_jwt.create_access_token.return_value = "new_access_token"
            mock_jwt.access_token_expire_minutes = 15
            mock_jwt_service.return_value = mock_jwt

            refresh_data = {"refresh_token": "valid_refresh_token"}
            response = client_instance.post("/auth/refresh", json=refresh_data)

            # Test API contract
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["access_token"]  # Token should exist and not be empty
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
            assert data["expires_in"] > 0  # Should have a positive expiration time

        # Clean up
        app.dependency_overrides.clear()

    def test_logout_revokes_token(self, client, mock_db):
        """Test that logout properly handles token revocation."""

        # Mock refresh token
        mock_token = MagicMock()
        mock_token.revoke = MagicMock()
        mock_db.set_query_result("scalars_results", [mock_token])

        logout_data = {"refresh_token": "valid_refresh_token"}
        response = client.post("/auth/logout", json=logout_data)

        # Test API contract
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        assert data["success"] is True

        # Verify token was revoked
        mock_token.revoke.assert_called_once()
        assert mock_db.committed  # Changes were committed

    def test_public_key_endpoint_works(self, client):
        """Test that public key endpoint returns expected format."""
        # Mock JWT service with public key
        with patch("app.services.jwt_service.get_jwt_service") as mock_jwt_service:
            mock_jwt = MagicMock()
            mock_jwt.public_key = "-----BEGIN PUBLIC KEY-----\nMOCK_KEY\n-----END PUBLIC KEY-----"
            mock_jwt_service.return_value = mock_jwt

            response = client.get("/auth/public-key")

            # Test API contract
            assert response.status_code == 200
            data = response.json()
            assert "BEGIN PUBLIC KEY" in data["public_key"]
            assert data["algorithm"] == "RS256"

    def test_invalid_json_returns_422(self, client):
        """Test that malformed JSON returns proper error code."""
        response = client.post(
            "/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_missing_fields_returns_422(self, client):
        """Test that missing required fields return proper error code."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"},  # Missing password
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
