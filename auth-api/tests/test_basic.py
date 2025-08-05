"""
Simple test to verify pytest is working.
"""

import os
from unittest.mock import patch

# Set environment variables
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_USERNAME"] = "test_user"
os.environ["DB_PASSWORD"] = "test_password"
os.environ["DB_NAME"] = "test_db"
os.environ["PRIVATE_KEY_PATH"] = "/tmp/test_private_key.pem"
os.environ["PUBLIC_KEY_PATH"] = "/tmp/test_public_key.pem"


def test_basic():
    """Basic test to verify pytest works."""
    assert 1 + 1 == 2


def test_environment_setup():
    """Test that environment variables are set correctly."""
    assert os.environ.get("JWT_SECRET_KEY") == "test_secret_key_for_testing_only"
    assert os.environ.get("DB_HOST") == "localhost"
    assert os.environ.get("DB_PORT") == "5432"


@patch("app.config.get_config")
def test_config_mocking(mock_get_config):
    """Test that we can mock the config."""
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.jwt_secret_key.get_secret_value.return_value = "test_secret"
    mock_get_config.return_value = mock_config

    # Import after mocking
    from app.config import get_config

    config = get_config()

    assert config.jwt_secret_key.get_secret_value() == "test_secret"
