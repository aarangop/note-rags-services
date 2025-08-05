from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    jwt_secret_key: SecretStr = Field(
        default=SecretStr("test_secret_key_for_testing_only"), description="JWT secret key for signing tokens", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="RS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=15, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=30, description="Refresh token expiration in days"
    )

    # RSA Key Configuration (for RS256)
    private_key_path: Path | None = Field(
        default=Path("/tmp/test_private_key.pem"),
        description="Path to RSA private key file",
        validation_alias="PRIVATE_KEY_PATH",
    )
    public_key_path: Path | None = Field(
        default=Path("/tmp/test_public_key.pem"), description="Path to RSA public key file", validation_alias="PUBLIC_KEY_PATH"
    )

    # Password Configuration
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_uppercase: bool = Field(
        default=True, description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True, description="Require lowercase letters in password"
    )
    password_require_numbers: bool = Field(default=True, description="Require numbers in password")
    password_require_symbols: bool = Field(default=False, description="Require symbols in password")

    # Security Configuration
    password_reset_token_expire_hours: int = Field(
        default=1, description="Password reset token expiration in hours"
    )
    verification_token_expire_hours: int = Field(
        default=24, description="Email verification token expiration in hours"
    )
    max_login_attempts: int = Field(default=5, description="Maximum login attempts before lockout")
    lockout_duration_minutes: int = Field(
        default=30, description="Account lockout duration in minutes"
    )

    # Database Configuration
    # Complete database URL (takes precedence if provided)
    db_full_url: str | None = Field(default=None, alias="DB_FULL_URL", description="Complete database URL")

    # Individual database connection components
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="test_user", alias="DB_USERNAME")
    db_password: SecretStr = Field(default=SecretStr("test_password"), alias="DB_PASSWORD")
    db_name: str = Field(default="note_rags_db", alias="DB_NAME")

    # Application Configuration
    app_name: str = Field(default="Auth API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode", validation_alias="DEBUG")
    log_level: str = Field(
        default="INFO", description="Logging level", validation_alias="LOG_LEVEL"
    )

    # Database configuration

    def get_private_key(self) -> str | None:
        """Get the RSA private key content."""
        if not self.private_key_path or not self.private_key_path.exists():
            return None
        return self.private_key_path.read_text()

    def get_public_key(self) -> str | None:
        """Get the RSA public key content."""
        if not self.public_key_path or not self.public_key_path.exists():
            return None
        return self.public_key_path.read_text()


config: Config | None = None


def get_config():
    global config
    if not config:
        config = Config()

    return config
