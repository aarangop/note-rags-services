from collections.abc import AsyncGenerator, Generator
from urllib.parse import quote_plus

from fastapi import Depends
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from .db import create_async_db_engine, create_db_engine


def build_database_url(
    database_url: str,
    dialect: str,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Build a database connection URL from CLI arguments."""
    if username and password:
        return f"{dialect}://{username}:{password}@{database_url}"
    return f"{dialect}://{database_url}"


class DBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")
    # Complete database URL (takes precedence if provided)
    db_url: str | None = Field(
        default=None, description="Complete database URL (overrides individual components)"
    )

    # Individual database connection components (used when db_url is not provided)
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int | None = Field(default=None, description="Database port")
    db_user: str | None = Field(default=None, description="Database username")
    db_password: SecretStr | None = Field(default=None, description="Database password")
    db_name: str | None = Field(default=None, description="Database name")
    db_dialect: str = Field(
        default="postgresql", description="Database dialect (e.g., postgresql, mysql, sqlite)"
    )
    db_driver: str | None = Field(
        default=None, description="Database driver (e.g., psycopg2, pymysql)"
    )

    @field_validator("db_dialect")
    @classmethod
    def validate_dialect(cls, v):
        if v is None:
            return v
        supported_dialects = ["postgresql", "mysql", "sqlite", "oracle", "mssql"]
        if v not in supported_dialects:
            raise ValueError(f"Unsupported dialect: {v}. Supported: {supported_dialects}")
        return v

    @field_validator("db_port")
    @classmethod
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    def model_post_init(self, __context) -> None:
        """Validate that either db_url is provided or required individual components are provided."""
        if not self.db_url:
            # If no complete URL provided, ensure required individual components are present
            if not self.db_user:
                raise ValueError("db_user is required when db_url is not provided")
            if not self.db_name:
                raise ValueError("db_name is required when db_url is not provided")
            if not self.db_dialect:
                raise ValueError("db_dialect is required when db_url is not provided")

    def get_db_url(self, async_driver: bool = False) -> str:
        """
        Generate database connection URL.

        Args:
            async_driver: If True, attempts to use async driver variant

        Returns:
            Complete database connection URL
        """
        if self.db_url:
            return self.db_url

        dialect = self.db_dialect
        driver = self._get_driver(async_driver)

        dialect_driver = f"{dialect}+{driver}" if driver else dialect

        username = quote_plus(self.db_user) if self.db_user else ""
        password = quote_plus(self.db_password.get_secret_value()) if self.db_password else ""

        if self.db_dialect == "sqlite":
            if driver:
                return f"sqlite+{driver}:///{self.db_name}"
            return f"sqlite:///{self.db_name}"

        host_port = self.db_host
        if self.db_port:
            host_port = f"{self.db_host}:{self.db_port}"

        return f"{dialect_driver}://{username}:{password}@{host_port}/{self.db_name}"

    def _get_driver(self, async_driver: bool = False) -> str | None:
        """Get appropriate driver based on dialect and async preference."""
        if self.db_driver:
            return self.db_driver

        driver_map = {
            "postgresql": {"sync": "psycopg2", "async": "asyncpg"},
            "mysql": {"sync": "pymysql", "async": "aiomysql"},
            "sqlite": {"sync": None, "async": "aiosqlite"},
        }

        dialect_drivers = driver_map.get(self.db_dialect, {})
        return dialect_drivers.get("async" if async_driver else "sync")

    def get_sync_url(self) -> str:
        """Get synchronous database URL."""
        return self.get_db_url(async_driver=False)

    def get_async_url(self) -> str:
        """Get asynchronous database URL."""
        return self.get_db_url(async_driver=True)

    def get_sync_session(self) -> Session:
        """
        Create and return a synchronous database session.

        Returns:
            SQLAlchemy Session instance
        """
        engine = create_db_engine(self.get_sync_url())
        session_factory = sessionmaker(bind=engine, class_=Session)
        return session_factory()

    def get_async_session(self) -> AsyncSession:
        """
        Create and return an asynchronous database session.

        Returns:
            SQLAlchemy AsyncSession instance
        """
        async_engine = create_async_db_engine(self.get_async_url())
        async_session_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession)
        return async_session_factory()


def get_db_config() -> DBConfig:
    """
    FastAPI dependency that provides database configuration.

    Returns:
        DBConfig: Database configuration instance
    """
    return DBConfig()


async def get_async_db_session(
    config: DBConfig = Depends(get_db_config),
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session with cleanup.

    Args:
        config: Database configuration instance

    Yields:
        AsyncSession: Database session for async operations
    """
    session = config.get_async_session()
    try:
        yield session
    finally:
        await session.close()


def get_sync_db_session(
    config: DBConfig = Depends(get_db_config),
) -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a sync database session with cleanup.

    Args:
        config: Database configuration instance

    Yields:
        Session: Database session for sync operations
    """
    session = config.get_sync_session()
    try:
        yield session
    finally:
        session.close()
