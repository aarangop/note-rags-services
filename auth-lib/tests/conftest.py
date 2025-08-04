import tempfile
import uuid
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_rsa_keys():
    """Generate test RSA key pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


@pytest.fixture
def key_files(temp_dir, test_rsa_keys):
    """Create temporary key files."""
    private_key_content, public_key_content = test_rsa_keys

    private_key_path = temp_dir / "private_key.pem"
    public_key_path = temp_dir / "public_key.pem"

    private_key_path.write_text(private_key_content)
    public_key_path.write_text(public_key_content)

    return private_key_path, public_key_path


@pytest.fixture
def test_user_data():
    """Sample user data for token creation."""
    return {
        "user_id": uuid.UUID("12345678-1234-5678-9012-123456789012"),
        "email": "test@example.com",
    }


@pytest.fixture
def sample_claims():
    """Sample additional claims for testing."""
    return {
        "role": "admin",
        "permissions": ["read", "write"],
        "custom_field": "test_value",
    }
