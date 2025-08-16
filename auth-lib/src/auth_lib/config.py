from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", extra="ignore", env_file_encoding="utf-8", case_sensitive=False
    )

    jwks_url: str = Field(default=..., alias="JWKS_URL")
    jwt_issuer: str = Field(default=..., alias="JWT_ISSUER")
    jwt_algorithm: str | None = Field(default="RS256", alias="JWT_ALGORITHM")

    jwt_verify_audience: bool = Field(default=False, alias="JWT_VERIFY_AUDIENCE")
    jwt_verify_expiration: bool = Field(default=True, alias="JWT_VERIFY_EXPIRATION")
    jwt_verify_issuer: bool = Field(default=True, alias="JWT_VERIFY_ISSUER")


def get_auth_settings():
    return AuthSettings()
