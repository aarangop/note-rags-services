import os
from unittest.mock import patch

from note_rags_db.config import Config


class TestConfig:
    """Test cases for the Config.get_url method."""

    def test_get_url_with_default_dialect(self):
        """Test get_url with default PostgreSQL dialect."""
        with patch.dict(
            os.environ,
            {
                "URL": "localhost:5432/testdb",
                "USER": "testuser",
                "PASSWORD": "testpass",
            },
        ):
            config = Config()
            expected_url = (
                "postgresql+psycopg2://testuser:testpass@localhost:5432/testdb"
            )
            assert config.get_url() == expected_url

    def test_get_url_with_custom_dialect(self):
        """Test get_url with custom dialect."""
        with patch.dict(
            os.environ,
            {
                "URL": "localhost:3306/mydb",
                "USER": "myuser",
                "PASSWORD": "mypass",
                "DIALECT": "mysql+pymysql",
            },
        ):
            config = Config()
            expected_url = "mysql+pymysql://myuser:mypass@localhost:3306/mydb"
            assert config.get_url() == expected_url

    def test_get_url_with_sqlite(self):
        """Test get_url with SQLite dialect."""
        with patch.dict(
            os.environ,
            {
                "URL": "/path/to/database.db",
                "USER": "",
                "PASSWORD": "",
                "DIALECT": "sqlite",
            },
        ):
            config = Config()
            expected_url = "sqlite://:@/path/to/database.db"
            assert config.get_url() == expected_url

    def test_get_url_with_special_characters_in_password(self):
        """Test get_url with special characters in password."""
        with patch.dict(
            os.environ,
            {
                "URL": "localhost:5432/testdb",
                "USER": "testuser",
                "PASSWORD": "p@ssw0rd!",
                "DIALECT": "postgresql",
            },
        ):
            config = Config()
            expected_url = "postgresql://testuser:p@ssw0rd!@localhost:5432/testdb"
            assert config.get_url() == expected_url
