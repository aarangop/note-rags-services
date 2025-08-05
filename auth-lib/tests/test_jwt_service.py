import datetime
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from jose import jwt
from src.auth_lib.jwt_service import JWTService, MissingPublicKeyError


class TestJWTService:
    """Test suite for JWTService class."""

    def test_initialization_with_existing_keys(self, key_files):
        """Test initialization when key files already exist."""
        private_key_path, public_key_path = key_files

        jwt_service = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_algorithm="RS256",
            jwt_access_token_expire_minutes=30,
            jwt_refresh_token_expire_days=14,
        )

        assert jwt_service.algorithm == "RS256"
        assert jwt_service.access_token_expire_minutes == 30
        assert jwt_service.refresh_token_expire_days == 14
        assert jwt_service.private_key is not None
        assert jwt_service.public_key is not None
        assert "-----BEGIN PRIVATE KEY-----" in jwt_service.private_key
        assert "-----BEGIN PUBLIC KEY-----" in jwt_service.public_key

    def test_initialization_with_nonexistent_keys_generates_new_ones(self, temp_dir):
        """Test initialization when key files don't exist generates new keys."""
        private_key_path = temp_dir / "new_private.pem"
        public_key_path = temp_dir / "new_public.pem"

        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        assert jwt_service.private_key is not None
        assert jwt_service.public_key is not None
        assert private_key_path.exists()
        assert public_key_path.exists()
        assert "-----BEGIN PRIVATE KEY-----" in jwt_service.private_key
        assert "-----BEGIN PUBLIC KEY-----" in jwt_service.public_key

    def test_initialization_defaults(self, key_files):
        """Test initialization with default values."""
        private_key_path, public_key_path = key_files

        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        assert jwt_service.algorithm == "RS256"
        assert jwt_service.access_token_expire_minutes == 15
        assert jwt_service.refresh_token_expire_days == 30

    @patch("src.jwt_service.logger")
    def test_initialization_key_loading_error_propagates(self, mock_logger, temp_dir):
        """Test that key initialization errors are properly propagated."""
        # Create a file that will cause permission errors
        private_key_path = temp_dir / "private.pem"
        public_key_path = temp_dir / "public.pem"

        # Write some content first
        private_key_path.write_text("invalid key")
        public_key_path.write_text("invalid key")

        with (
            patch.object(Path, "read_text", side_effect=PermissionError("Access denied")),
            pytest.raises(PermissionError),
        ):
            JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

    def test_create_access_token_success(self, key_files, test_user_data):
        """Test successful access token creation."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_access_token_expire_minutes=60,
        )

        token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token structure
        assert jwt_service.public_key
        decoded = jwt.decode(token, jwt_service.public_key, algorithms=["RS256"])
        assert decoded["sub"] == str(test_user_data["user_id"])
        assert decoded["email"] == test_user_data["email"]
        assert decoded["type"] == "access"
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded

    def test_create_access_token_with_additional_claims(
        self, key_files, test_user_data, sample_claims
    ):
        """Test access token creation with additional claims."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"],
            email=test_user_data["email"],
            additional_claims=sample_claims,
        )

        assert jwt_service.public_key
        decoded = jwt.decode(token, jwt_service.public_key, algorithms=["RS256"])
        assert decoded["role"] == "admin"
        assert decoded["permissions"] == ["read", "write"]
        assert decoded["custom_field"] == "test_value"
        # Protected claims should still be present
        assert decoded["sub"] == str(test_user_data["user_id"])
        assert decoded["email"] == test_user_data["email"]
        assert decoded["type"] == "access"

    def test_create_access_token_without_private_key_raises_error(self, key_files, test_user_data):
        """Test that creating access token without private key raises appropriate error."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)
        jwt_service.private_key = None  # Simulate missing private key

        with pytest.raises(Exception, match="Missing private key"):
            jwt_service.create_access_token(
                user_id=test_user_data["user_id"], email=test_user_data["email"]
            )

    def test_create_refresh_token_success(self, key_files, test_user_data):
        """Test successful refresh token creation."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_refresh_token_expire_days=7,
        )

        token = jwt_service.create_refresh_token(user_id=test_user_data["user_id"])

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify token structure
        assert jwt_service.public_key
        decoded = jwt.decode(token, jwt_service.public_key, algorithms=["RS256"])
        assert decoded["sub"] == str(test_user_data["user_id"])
        assert decoded["type"] == "refresh"
        assert "jti" in decoded
        assert "iat" in decoded
        assert "exp" in decoded
        # Should not have email in refresh token
        assert "email" not in decoded

    def test_create_refresh_token_without_private_key_raises_error(self, key_files, test_user_data):
        """Test that creating refresh token without private key raises appropriate error."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)
        jwt_service.private_key = None  # Simulate missing private key

        with pytest.raises(Exception, match="Missing private key"):
            jwt_service.create_refresh_token(user_id=test_user_data["user_id"])

    def test_verify_token_success(self, key_files, test_user_data):
        """Test successful token verification."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        # Create a token first
        token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        # Verify the token
        payload = jwt_service.verify_token(token)

        assert payload["sub"] == str(test_user_data["user_id"])
        assert payload["email"] == test_user_data["email"]
        assert payload["type"] == "access"

    def test_verify_token_without_public_key_raises_error(self, key_files, test_user_data):
        """Test that verifying token without public key raises appropriate error."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        # Create a token first
        token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        jwt_service.public_key = None  # Simulate missing public key

        with pytest.raises(MissingPublicKeyError):
            jwt_service.verify_token(token)

    def test_verify_invalid_token_raises_error(self, key_files):
        """Test that verifying invalid token raises appropriate error."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        with pytest.raises((Exception, OSError)):
            jwt_service.verify_token("invalid.token.here")

    def test_verify_expired_token_raises_error(self, key_files, test_user_data):
        """Test that verifying expired token raises appropriate error."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_access_token_expire_minutes=-1,  # Expired 1 minute ago
        )

        token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        # Token should be expired
        with pytest.raises((Exception, OSError)):
            jwt_service.verify_token(token)

    def test_token_expiration_times(self, key_files, test_user_data):
        """Test that tokens have correct expiration times."""
        private_key_path, public_key_path = key_files
        access_expire_minutes = 30
        refresh_expire_days = 7

        jwt_service = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_access_token_expire_minutes=access_expire_minutes,
            jwt_refresh_token_expire_days=refresh_expire_days,
        )

        # Test access token expiration
        access_token = jwt_service.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )
        assert jwt_service.public_key
        access_payload = jwt.decode(access_token, jwt_service.public_key, algorithms=["RS256"])
        access_exp = datetime.datetime.fromtimestamp(access_payload["exp"])
        access_iat = datetime.datetime.fromtimestamp(access_payload["iat"])
        access_duration = access_exp - access_iat

        # Allow some tolerance for execution time
        assert abs(access_duration.total_seconds() - (access_expire_minutes * 60)) < 5

        # Test refresh token expiration
        refresh_token = jwt_service.create_refresh_token(user_id=test_user_data["user_id"])
        refresh_payload = jwt.decode(refresh_token, jwt_service.public_key, algorithms=["RS256"])
        refresh_exp = datetime.datetime.fromtimestamp(refresh_payload["exp"])
        refresh_iat = datetime.datetime.fromtimestamp(refresh_payload["iat"])
        refresh_duration = refresh_exp - refresh_iat

        # Allow some tolerance for execution time
        assert abs(refresh_duration.total_seconds() - (refresh_expire_days * 24 * 3600)) < 5

    def test_key_generation_creates_valid_rsa_keys(self, temp_dir):
        """Test that generated RSA keys are valid and can be used for JWT operations."""
        private_key_path = temp_dir / "generated_private.pem"
        public_key_path = temp_dir / "generated_public.pem"

        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        # Keys should be generated and saved
        assert private_key_path.exists()
        assert public_key_path.exists()

        # Test that the keys work for JWT operations
        user_id = uuid.uuid4()
        email = "test@example.com"

        token = jwt_service.create_access_token(user_id=user_id, email=email)
        payload = jwt_service.verify_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["email"] == email

    def test_different_algorithms_support(self, key_files, test_user_data):
        """Test that different JWT algorithms work correctly."""
        private_key_path, public_key_path = key_files

        # Test with RS256 (default)
        jwt_service_rs256 = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_algorithm="RS256",
        )

        token_rs256 = jwt_service_rs256.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        payload_rs256 = jwt_service_rs256.verify_token(token_rs256)
        assert payload_rs256["sub"] == str(test_user_data["user_id"])

        # Test with RS512
        jwt_service_rs512 = JWTService(
            private_key_path=private_key_path,
            public_key_path=public_key_path,
            jwt_algorithm="RS512",
        )

        token_rs512 = jwt_service_rs512.create_access_token(
            user_id=test_user_data["user_id"], email=test_user_data["email"]
        )

        payload_rs512 = jwt_service_rs512.verify_token(token_rs512)
        assert payload_rs512["sub"] == str(test_user_data["user_id"])

    def test_unique_jti_in_tokens(self, key_files, test_user_data):
        """Test that each token gets a unique JTI (JWT ID)."""
        private_key_path, public_key_path = key_files
        jwt_service = JWTService(private_key_path=private_key_path, public_key_path=public_key_path)

        # Create multiple tokens
        tokens = []
        for _ in range(5):
            token = jwt_service.create_access_token(
                user_id=test_user_data["user_id"], email=test_user_data["email"]
            )
            tokens.append(token)

        # Decode all tokens and check JTIs are unique
        jtis = []
        for token in tokens:
            assert jwt_service.public_key
            payload = jwt.decode(token, jwt_service.public_key, algorithms=["RS256"])
            jtis.append(payload["jti"])

        assert len(set(jtis)) == len(jtis)  # All JTIs should be unique

    def test_get_private_key_file_not_exists(self, temp_dir):
        """Test _get_private_key returns None when file doesn't exist."""
        private_key_path = temp_dir / "nonexistent.pem"
        public_key_path = temp_dir / "public.pem"
        public_key_path.write_text("dummy")

        jwt_service = JWTService.__new__(JWTService)  # Create without calling __init__
        jwt_service.private_key_path = private_key_path
        jwt_service.public_key_path = public_key_path

        result = jwt_service._get_private_key()
        assert result is None

    def test_get_public_key_file_not_exists(self, temp_dir):
        """Test _get_public_key returns None when file doesn't exist."""
        private_key_path = temp_dir / "private.pem"
        public_key_path = temp_dir / "nonexistent.pem"
        private_key_path.write_text("dummy")

        jwt_service = JWTService.__new__(JWTService)  # Create without calling __init__
        jwt_service.private_key_path = private_key_path
        jwt_service.public_key_path = public_key_path

        result = jwt_service._get_public_key()
        assert result is None
