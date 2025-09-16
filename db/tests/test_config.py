from unittest.mock import Mock, patch

import pytest
from note_rags_db.config import DBConfig, build_database_url
from pydantic import SecretStr, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class TestDBConfig:
    """Test cases for DBConfig class."""

    def test_postgresql_sync_url(self):
        """Test PostgreSQL synchronous URL generation."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )
        expected = "postgresql+psycopg2://testuser:testpass@localhost:5432/testdb"
        assert config.get_sync_url() == expected

    def test_postgresql_async_url(self):
        """Test PostgreSQL asynchronous URL generation."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )
        expected = "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
        assert config.get_async_url() == expected

    def test_sqlite_sync_url(self):
        """Test SQLite synchronous URL generation."""
        config = DBConfig(
            db_host="localhost",
            db_user="dummy",
            db_password=SecretStr("dummy"),
            db_name="test.db",
            db_dialect="sqlite",
        )
        expected = "sqlite:///test.db"
        assert config.get_sync_url() == expected

    def test_sqlite_async_url(self):
        """Test SQLite asynchronous URL generation."""
        config = DBConfig(
            db_host="localhost",
            db_user="dummy",
            db_password=SecretStr("dummy"),
            db_name="test.db",
            db_dialect="sqlite",
        )
        expected = "sqlite+aiosqlite:///test.db"
        assert config.get_async_url() == expected

    def test_custom_driver(self):
        """Test custom driver specification."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
            db_driver="pg8000",
        )
        expected = "postgresql+pg8000://testuser:testpass@localhost:5432/testdb"
        assert config.get_db_url() == expected

    def test_no_port_specified(self):
        """Test URL generation without port."""
        config = DBConfig(
            db_host="example.com",
            db_user="user",
            db_password=SecretStr("pass"),
            db_name="db",
            db_dialect="postgresql",
        )
        expected = "postgresql+psycopg2://user:pass@example.com/db"
        assert config.get_db_url() == expected

    def test_override_with_complete_url(self):
        """Test that db_url overrides individual components."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
            db_url="postgresql://override:password@override.com:1234/override_db",
        )
        expected = "postgresql://override:password@override.com:1234/override_db"
        assert config.get_db_url() == expected

    def test_url_encoding_special_characters(self):
        """Test proper URL encoding of special characters in credentials."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="user@domain.com",
            db_password=SecretStr("p@ss!word#123"),
            db_name="testdb",
            db_dialect="postgresql",
        )
        expected = (
            "postgresql+psycopg2://user%40domain.com:p%40ss%21word%23123@localhost:5432/testdb"
        )
        assert config.get_db_url() == expected

    def test_validate_supported_dialects(self):
        """Test validation of supported database dialects."""
        valid_dialects = ["postgresql", "mysql", "sqlite", "oracle", "mssql"]

        for dialect in valid_dialects:
            config = DBConfig(
                db_host="localhost",
                db_user="user",
                db_password=SecretStr("pass"),
                db_name="db",
                db_dialect=dialect,
            )
            assert config.db_dialect == dialect

    def test_validate_unsupported_dialect(self):
        """Test validation error for unsupported dialect."""
        with pytest.raises(ValidationError) as exc_info:
            DBConfig(
                db_host="localhost",
                db_user="user",
                db_password=SecretStr("pass"),
                db_name="db",
                db_dialect="unsupported",
            )

        assert "Unsupported dialect" in str(exc_info.value)

    def test_validate_port_range(self):
        """Test port validation."""
        valid_ports = [1, 5432, 3306, 65535]

        for port in valid_ports:
            config = DBConfig(
                db_host="localhost",
                db_port=port,
                db_user="user",
                db_password=SecretStr("pass"),
                db_name="db",
                db_dialect="postgresql",
            )
            assert config.db_port == port

    def test_validate_invalid_port(self):
        """Test validation error for invalid ports."""
        invalid_ports = [0, -1, 65536, 100000]

        for port in invalid_ports:
            with pytest.raises(ValidationError) as exc_info:
                DBConfig(
                    db_host="localhost",
                    db_port=port,
                    db_user="user",
                    db_password=SecretStr("pass"),
                    db_name="db",
                    db_dialect="postgresql",
                )

            assert "Port must be between 1 and 65535" in str(exc_info.value)

    def test_get_driver_with_unknown_dialect(self):
        """Test driver selection for unknown dialect."""
        config = DBConfig(
            db_host="localhost",
            db_user="user",
            db_password=SecretStr("pass"),
            db_name="db",
            db_dialect="oracle",  # Not in driver map
        )

        # Should return None for unknown dialects
        assert config._get_driver(async_driver=False) is None
        assert config._get_driver(async_driver=True) is None

    def test_password_secrecy(self):
        """Test that password is handled as SecretStr."""
        config = DBConfig(
            db_host="localhost",
            db_user="user",
            db_password=SecretStr("secretpass"),
            db_name="db",
            db_dialect="postgresql",
        )

        # Password should not be visible in string representation
        config_str = str(config)
        assert "secretpass" not in config_str
        assert "**********" in config_str or "[SecretStr]" in config_str

    def test_get_db_url_method_variants(self):
        """Test different URL generation methods return consistent results."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )

        sync_url_1 = config.get_db_url(async_driver=False)
        sync_url_2 = config.get_sync_url()
        async_url_1 = config.get_db_url(async_driver=True)
        async_url_2 = config.get_async_url()

        assert sync_url_1 == sync_url_2
        assert async_url_1 == async_url_2
        assert sync_url_1 != async_url_1


class TestBuildDatabaseUrl:
    """Test cases for build_database_url function."""

    def test_with_credentials(self):
        """Test URL building with username and password."""
        result = build_database_url(
            database_url="localhost:5432/mydb",
            dialect="postgresql",
            username="user",
            password="pass",
        )
        expected = "postgresql://user:pass@localhost:5432/mydb"
        assert result == expected

    def test_without_credentials(self):
        """Test URL building without credentials."""
        result = build_database_url(database_url="localhost:5432/mydb", dialect="postgresql")
        expected = "postgresql://localhost:5432/mydb"
        assert result == expected

    def test_partial_credentials(self):
        """Test URL building with only username or password."""
        result = build_database_url(
            database_url="localhost:5432/mydb", dialect="postgresql", username="user"
        )
        expected = "postgresql://localhost:5432/mydb"
        assert result == expected

        result = build_database_url(
            database_url="localhost:5432/mydb", dialect="postgresql", password="pass"
        )
        expected = "postgresql://localhost:5432/mydb"
        assert result == expected


@pytest.fixture
def postgres_config():
    """Fixture for PostgreSQL configuration."""
    return DBConfig(
        db_host="localhost",
        db_port=5432,
        db_user="postgres",
        db_password=SecretStr("postgres"),
        db_name="testdb",
        db_dialect="postgresql",
    )


@pytest.fixture
def sqlite_config():
    """Fixture for SQLite configuration."""
    return DBConfig(
        db_host="localhost",
        db_user="dummy",
        db_password=SecretStr("dummy"),
        db_name="test.db",
        db_dialect="sqlite",
    )


class TestConfigIntegration:
    """Integration tests using fixtures."""

    def test_postgres_urls(self, postgres_config):
        """Test PostgreSQL URL generation using fixture."""
        sync_url = postgres_config.get_sync_url()
        async_url = postgres_config.get_async_url()

        assert "postgresql+psycopg2" in sync_url
        assert "postgresql+asyncpg" in async_url
        assert "localhost:5432" in sync_url
        assert "localhost:5432" in async_url

    def test_sqlite_urls(self, sqlite_config):
        """Test SQLite URL generation using fixture."""
        sync_url = sqlite_config.get_sync_url()
        async_url = sqlite_config.get_async_url()

        assert sync_url == "sqlite:///test.db"
        assert async_url == "sqlite+aiosqlite:///test.db"


class TestDBSessions:
    """Test cases for database session creation."""

    @patch("note_rags_db.config.create_db_engine")
    @patch("note_rags_db.config.sessionmaker")
    def test_get_sync_session_creation(self, mock_sessionmaker, mock_create_engine):
        """Test that get_sync_session creates session correctly."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_session = Mock(spec=Session)
        mock_session_factory.return_value = mock_session
        mock_sessionmaker.return_value = mock_session_factory

        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )

        result = config.get_sync_session()

        # Verify the URL passed to create_db_engine
        mock_create_engine.assert_called_once()
        call_args = mock_create_engine.call_args[0][0]
        assert "postgresql+psycopg2" in call_args
        assert "testuser:testpass@localhost:5432/testdb" in call_args

        # Verify sessionmaker is called correctly
        mock_sessionmaker.assert_called_once_with(bind=mock_engine, class_=Session)

        # Verify session factory is called
        mock_session_factory.assert_called_once()

        assert result == mock_session

    @patch("note_rags_db.config.create_async_db_engine")
    @patch("note_rags_db.config.async_sessionmaker")
    def test_get_async_session_creation(self, mock_async_sessionmaker, mock_create_async_engine):
        """Test that get_async_session creates session correctly."""
        mock_async_engine = Mock()
        mock_create_async_engine.return_value = mock_async_engine
        mock_async_session_factory = Mock()
        mock_async_session = Mock(spec=AsyncSession)
        mock_async_session_factory.return_value = mock_async_session
        mock_async_sessionmaker.return_value = mock_async_session_factory

        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )

        result = config.get_async_session()

        # Verify the URL passed to create_async_db_engine
        mock_create_async_engine.assert_called_once()
        call_args = mock_create_async_engine.call_args[0][0]
        assert "postgresql+asyncpg" in call_args
        assert "testuser:testpass@localhost:5432/testdb" in call_args

        # Verify async_sessionmaker is called correctly
        mock_async_sessionmaker.assert_called_once_with(bind=mock_async_engine, class_=AsyncSession)

        # Verify session factory is called
        mock_async_session_factory.assert_called_once()

        assert result == mock_async_session

    def test_session_url_generation_postgresql(self):
        """Test URL generation for PostgreSQL sessions."""
        config = DBConfig(
            db_host="localhost",
            db_port=5432,
            db_user="testuser",
            db_password=SecretStr("testpass"),
            db_name="testdb",
            db_dialect="postgresql",
        )

        sync_url = config.get_sync_url()
        async_url = config.get_async_url()

        assert sync_url == "postgresql+psycopg2://testuser:testpass@localhost:5432/testdb"
        assert async_url == "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"
