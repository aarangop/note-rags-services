"""Integration tests demonstrating the full JWT workflow."""

import uuid

import pytest
from src.jwt_service import JWTConfig, JWTServiceBuilder


class TestJWTIntegration:
    """Integration tests for JWT service components working together."""

    def test_full_jwt_workflow(self, temp_dir):
        """Test complete JWT workflow: build service, create tokens, verify tokens."""
        # Setup paths
        private_key_path = temp_dir / "jwt_private.pem"
        public_key_path = temp_dir / "jwt_public.pem"

        # Build JWT service using the builder pattern
        jwt_service = (
            JWTServiceBuilder(None)
            .set_jwt_algorithm("RS256")
            .set_jwt_access_token_expire_minutes(60)
            .set_jwt_refresh_token_expire_days(7)
            .set_private_key_path(private_key_path)
            .set_public_key_path(public_key_path)
            .build()
        )

        # Test user data
        user_id = uuid.UUID("12345678-1234-5678-9012-123456789012")
        email = "integration@example.com"
        additional_claims = {"role": "admin", "department": "engineering"}

        # Create access token
        access_token = jwt_service.create_access_token(
            user_id=user_id, email=email, additional_claims=additional_claims
        )

        # Create refresh token
        refresh_token = jwt_service.create_refresh_token(user_id=user_id)

        # Verify access token
        access_payload = jwt_service.verify_token(access_token)
        assert access_payload["sub"] == str(user_id)
        assert access_payload["email"] == email
        assert access_payload["type"] == "access"
        assert access_payload["role"] == "admin"
        assert access_payload["department"] == "engineering"

        # Verify refresh token
        refresh_payload = jwt_service.verify_token(refresh_token)
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["type"] == "refresh"
        assert "email" not in refresh_payload  # Refresh tokens don't include email

        # Verify keys were created on disk
        assert private_key_path.exists()
        assert public_key_path.exists()

        # Verify key files contain valid PEM data
        private_content = private_key_path.read_text()
        public_content = public_key_path.read_text()
        assert "-----BEGIN PRIVATE KEY-----" in private_content
        assert "-----END PRIVATE KEY-----" in private_content
        assert "-----BEGIN PUBLIC KEY-----" in public_content
        assert "-----END PUBLIC KEY-----" in public_content

    def test_service_reuse_existing_keys(self, key_files):
        """Test that service can reuse existing key files."""
        private_key_path, public_key_path = key_files

        # Create first service instance
        service1 = (
            JWTServiceBuilder(None)
            .set_private_key_path(private_key_path)
            .set_public_key_path(public_key_path)
            .build()
        )

        user_id = uuid.uuid4()
        email = "test@example.com"

        # Create token with first service
        token = service1.create_access_token(user_id=user_id, email=email)

        # Create second service instance with same key paths
        service2 = (
            JWTServiceBuilder(None)
            .set_private_key_path(private_key_path)
            .set_public_key_path(public_key_path)
            .build()
        )

        # Second service should be able to verify token created by first service
        payload = service2.verify_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email

    def test_custom_config_integration(self, temp_dir):
        """Test integration using custom JWTConfig."""
        private_key_path = temp_dir / "custom_private.pem"
        public_key_path = temp_dir / "custom_public.pem"

        # Create custom config
        config = JWTConfig(
            jwt_algorithm="RS512",  # Different algorithm
            jwt_access_token_expire_minutes=120,
            jwt_refresh_token_expire_days=14,
            private_key_path=private_key_path,
            public_key_path=public_key_path,
        )

        # Build service with custom config
        jwt_service = JWTServiceBuilder(config).build()

        # Verify service uses custom configuration
        assert jwt_service.algorithm == "RS512"
        assert jwt_service.access_token_expire_minutes == 120
        assert jwt_service.refresh_token_expire_days == 14

        # Test token operations work with custom config
        user_id = uuid.uuid4()
        email = "custom@example.com"

        token = jwt_service.create_access_token(user_id=user_id, email=email)
        payload = jwt_service.verify_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["email"] == email

    def test_multiple_services_different_configs(self, temp_dir):
        """Test multiple services with different configurations."""
        # Service 1: Short-lived tokens
        service1 = (
            JWTServiceBuilder(None)
            .set_jwt_access_token_expire_minutes(5)
            .set_jwt_refresh_token_expire_days(1)
            .set_private_key_path(temp_dir / "service1_private.pem")
            .set_public_key_path(temp_dir / "service1_public.pem")
            .build()
        )

        # Service 2: Long-lived tokens
        service2 = (
            JWTServiceBuilder(None)
            .set_jwt_access_token_expire_minutes(240)
            .set_jwt_refresh_token_expire_days(30)
            .set_private_key_path(temp_dir / "service2_private.pem")
            .set_public_key_path(temp_dir / "service2_public.pem")
            .build()
        )

        user_id = uuid.uuid4()
        email = "multi@example.com"

        # Create tokens with both services
        token1 = service1.create_access_token(user_id=user_id, email=email)
        token2 = service2.create_access_token(user_id=user_id, email=email)

        # Each service can verify its own tokens
        payload1 = service1.verify_token(token1)
        payload2 = service2.verify_token(token2)

        assert payload1["sub"] == str(user_id)
        assert payload2["sub"] == str(user_id)

        # But services cannot verify each other's tokens (different keys)
        with pytest.raises(Exception):
            service1.verify_token(token2)

        with pytest.raises(Exception):
            service2.verify_token(token1)
