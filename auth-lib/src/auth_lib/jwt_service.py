import datetime
import uuid
from pathlib import Path
from typing import Any

import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from pydantic import Field
from pydantic_settings import BaseSettings

logger = structlog.get_logger(__name__)


class MissingPrivateKeyError(Exception):
    message = "Missing private key"


class MissingPublicKeyError(Exception):
    message = "Missing public key"


class JWTConfig(BaseSettings):
    jwt_algorithm: str = Field(default=...)
    jwt_access_token_expire_minutes: int = Field(
        default=15, description="Access token expiration in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=30, description="Refresh token expiration in days"
    )
    private_key_path: Path | None = Field(default=None, description="Path to RSA public key")
    public_key_path: Path | None = Field(default=None, description="Path to RSA public key")


class JWTServiceBuilder:
    def __init__(self, config: JWTConfig | None = None):
        self.config = (
            config
            if config
            else JWTConfig(
                jwt_algorithm="RS256",
                jwt_access_token_expire_minutes=15,
                jwt_refresh_token_expire_days=30,
            )
        )

    def set_jwt_algorithm(self, algorithm: str) -> "JWTServiceBuilder":
        self.config.jwt_algorithm = algorithm
        return self

    def set_jwt_access_token_expire_minutes(self, minutes: int) -> "JWTServiceBuilder":
        self.config.jwt_access_token_expire_minutes = minutes
        return self

    def set_jwt_refresh_token_expire_days(self, days: int) -> "JWTServiceBuilder":
        self.config.jwt_refresh_token_expire_days = days
        return self

    def set_private_key_path(self, path: Path) -> "JWTServiceBuilder":
        self.config.private_key_path = path
        return self

    def set_public_key_path(self, path: Path) -> "JWTServiceBuilder":
        self.config.public_key_path = path
        return self

    def build(self) -> "JWTService":
        if not self.config.private_key_path:
            raise Exception("Private key path not provided")
        if not self.config.public_key_path:
            raise Exception("Public key path not provided")

        return JWTService(
            private_key_path=self.config.private_key_path,
            public_key_path=self.config.public_key_path,
            jwt_algorithm=self.config.jwt_algorithm,
            jwt_access_token_expire_minutes=self.config.jwt_access_token_expire_minutes,
            jwt_refresh_token_expire_days=self.config.jwt_refresh_token_expire_days,
        )


class JWTService:
    def __init__(
        self,
        private_key_path: Path,
        public_key_path: Path,
        jwt_algorithm: str = "RS256",
        jwt_access_token_expire_minutes: int = 15,
        jwt_refresh_token_expire_days: int = 30,
    ):
        self.algorithm = jwt_algorithm
        self.access_token_expire_minutes = jwt_access_token_expire_minutes
        self.refresh_token_expire_days = jwt_refresh_token_expire_days

        # Initialize RSA keys
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.private_key = None
        self.public_key = None
        self._initialize_keys()

    def _initialize_keys(self) -> None:
        try:
            private_key_content = self._get_private_key()
            public_key_content = self._get_public_key()

            if private_key_content and public_key_content:
                self.private_key = private_key_content
                self.public_key = public_key_content
                logger.info("Loaded existing RSA keys from files")
            else:
                self._generate_keys()
                logger.info("Generated new RSA keys")

        except Exception as e:
            logger.error("Failed to initialize RSA keys", error=e)
            raise e

    def _generate_keys(self) -> None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.private_key = private_pem.decode("utf-8")
        self.public_key = public_pem.decode("utf-8")

        if self.private_key_path:
            self.private_key_path.parent.mkdir(parents=True, exist_ok=True)
            self.private_key_path.write_text(self.private_key)

        if self.public_key_path:
            self.public_key_path.parent.mkdir(parents=True, exist_ok=True)
            self.public_key_path.write_text(self.public_key)

    def _get_private_key(self) -> str | None:
        """Get the RSA private key content."""
        if not self.private_key_path or not self.private_key_path.exists():
            return None
        return self.private_key_path.read_text()

    def _get_public_key(self) -> str | None:
        """Get the RSA public key content."""
        if not self.public_key_path or not self.public_key_path.exists():
            return None
        return self.public_key_path.read_text()

    def create_access_token(
        self, user_id: uuid.UUID, email: str, additional_claims: dict[str, Any] | None = None
    ) -> str:
        now = datetime.datetime.now(datetime.UTC)
        expire = now + datetime.timedelta(minutes=self.access_token_expire_minutes)

        protected_claims = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": expire,
            "type": "access",
            "jti": str(uuid.uuid4()),
        }

        payload = additional_claims.copy() if additional_claims else {}
        payload.update(protected_claims)

        try:
            if not self.private_key:
                raise MissingPrivateKeyError()
            token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
            logger.info("Created access token", user_id=str(user_id))
            return token
        except MissingPrivateKeyError as e:
            logger.error("Failed to create access token due to missing private key")
            raise Exception(e.message) from e
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise e

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        now = datetime.datetime.now(datetime.UTC)
        expire = now + datetime.timedelta(days=self.refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": expire,
            "type": "refresh",
            "jti": str(uuid.uuid4()),
        }

        try:
            if not self.private_key:
                raise MissingPrivateKeyError()
            token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
            logger.info("Created refresh token", user_id=str(user_id), expires_at=expire)
            return token
        except MissingPrivateKeyError as e:
            logger.error("Failed to create refresh token due to missing private key")
            raise Exception(e.message) from e
        except Exception as e:
            logger.error("Failed to create refresh token", user_id=str(user_id), error=str(e))
            raise

    def verify_token(self, token: str) -> dict[str, Any]:
        try:
            if not self.public_key:
                raise MissingPublicKeyError
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
            return payload
        except MissingPublicKeyError as e:
            logger.error("Failed to verify token due to missing public key")
            raise e
        except Exception as e:
            logger.error("Failed to verify token", error=e)
            raise e

    def get_user_id_from_token(self, token: str) -> uuid.UUID | None:
        """
        Extract user ID from a valid token.

        Args:
            token: JWT token string

        Returns:
            User UUID if token is valid, None if invalid
        """
        try:
            payload = self.verify_token(token)
            user_id_str = payload.get("sub")
            if user_id_str:
                return uuid.UUID(user_id_str)
            return None
        except Exception as e:
            logger.warning("Failed to extract ID from token", error=e)
            return None
