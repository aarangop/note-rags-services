from pathlib import Path

import pytest
from src.auth_lib.jwt_service import JWTConfig, JWTService, JWTServiceBuilder


class TestJWTServiceBuilder:
    """Test suite for JWTServiceBuilder class."""

    def test_builder_with_no_config_uses_defaults(self):
        """Test that builder with None config uses default values."""
        builder = JWTServiceBuilder(None)

        assert builder.config.jwt_algorithm == "RS256"
        assert builder.config.jwt_access_token_expire_minutes == 15
        assert builder.config.jwt_refresh_token_expire_days == 30
        assert builder.config.private_key_path is None
        assert builder.config.public_key_path is None

    def test_builder_with_provided_config(self):
        """Test that builder uses provided config."""
        config = JWTConfig(
            jwt_algorithm="HS256",
            jwt_access_token_expire_minutes=30,
            jwt_refresh_token_expire_days=7,
            private_key_path=Path("/path/to/private.pem"),
            public_key_path=Path("/path/to/public.pem"),
        )
        builder = JWTServiceBuilder(config)

        assert builder.config == config
        assert builder.config.jwt_algorithm == "HS256"
        assert builder.config.jwt_access_token_expire_minutes == 30
        assert builder.config.jwt_refresh_token_expire_days == 7

    def test_set_jwt_algorithm_returns_builder(self):
        """Test that set_jwt_algorithm returns the builder for chaining."""
        builder = JWTServiceBuilder(None)
        result = builder.set_jwt_algorithm("HS256")

        assert result is builder
        assert builder.config.jwt_algorithm == "HS256"

    def test_set_access_token_expire_minutes_returns_builder(self):
        """Test that set_jwt_access_token_expire_minutes returns the builder for chaining."""
        builder = JWTServiceBuilder(None)
        result = builder.set_jwt_access_token_expire_minutes(60)

        assert result is builder
        assert builder.config.jwt_access_token_expire_minutes == 60

    def test_set_refresh_token_expire_days_returns_builder(self):
        """Test that set_jwt_refresh_token_expire_days returns the builder for chaining."""
        builder = JWTServiceBuilder(None)
        result = builder.set_jwt_refresh_token_expire_days(7)

        assert result is builder
        assert builder.config.jwt_refresh_token_expire_days == 7

    def test_set_private_key_path_returns_builder(self):
        """Test that set_private_key_path returns the builder for chaining."""
        builder = JWTServiceBuilder(None)
        path = Path("/path/to/private.pem")
        result = builder.set_private_key_path(path)

        assert result is builder
        assert builder.config.private_key_path == path

    def test_set_public_key_path_returns_builder(self):
        """Test that set_public_key_path returns the builder for chaining."""
        builder = JWTServiceBuilder(None)
        path = Path("/path/to/public.pem")
        result = builder.set_public_key_path(path)

        assert result is builder
        assert builder.config.public_key_path == path

    def test_builder_method_chaining(self):
        """Test that all builder methods can be chained together."""
        builder = JWTServiceBuilder(None)
        private_path = Path("/path/to/private.pem")
        public_path = Path("/path/to/public.pem")

        result = (
            builder.set_jwt_algorithm("HS256")
            .set_jwt_access_token_expire_minutes(60)
            .set_jwt_refresh_token_expire_days(7)
            .set_private_key_path(private_path)
            .set_public_key_path(public_path)
        )

        assert result is builder
        assert builder.config.jwt_algorithm == "HS256"
        assert builder.config.jwt_access_token_expire_minutes == 60
        assert builder.config.jwt_refresh_token_expire_days == 7
        assert builder.config.private_key_path == private_path
        assert builder.config.public_key_path == public_path

    def test_build_without_private_key_path_raises_exception(self):
        """Test that build raises exception when private key path is not set."""
        builder = JWTServiceBuilder(None)
        builder.set_public_key_path(Path("/path/to/public.pem"))

        with pytest.raises(Exception, match="Private key path not provided"):
            builder.build()

    def test_build_without_public_key_path_raises_exception(self):
        """Test that build raises exception when public key path is not set."""
        builder = JWTServiceBuilder(None)
        builder.set_private_key_path(Path("/path/to/private.pem"))

        with pytest.raises(Exception, match="Public key path not provided"):
            builder.build()

    def test_build_creates_jwt_service_with_correct_parameters(self, key_files):
        """Test that build creates JWTService with correct parameters."""
        private_key_path, public_key_path = key_files

        builder = JWTServiceBuilder(None)
        jwt_service = (
            builder.set_jwt_algorithm("RS256")
            .set_jwt_access_token_expire_minutes(30)
            .set_jwt_refresh_token_expire_days(14)
            .set_private_key_path(private_key_path)
            .set_public_key_path(public_key_path)
            .build()
        )

        assert isinstance(jwt_service, JWTService)
        assert jwt_service.algorithm == "RS256"
        assert jwt_service.access_token_expire_minutes == 30
        assert jwt_service.refresh_token_expire_days == 14
        assert jwt_service.private_key_path == private_key_path
        assert jwt_service.public_key_path == public_key_path

    def test_build_with_custom_config(self, key_files):
        """Test that build works with a custom config."""
        private_key_path, public_key_path = key_files

        config = JWTConfig(
            jwt_algorithm="RS256",
            jwt_access_token_expire_minutes=45,
            jwt_refresh_token_expire_days=21,
            private_key_path=private_key_path,
            public_key_path=public_key_path,
        )

        builder = JWTServiceBuilder(config)
        jwt_service = builder.build()

        assert isinstance(jwt_service, JWTService)
        assert jwt_service.algorithm == "RS256"
        assert jwt_service.access_token_expire_minutes == 45
        assert jwt_service.refresh_token_expire_days == 21
