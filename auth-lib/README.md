# Auth Library

A Python JWT authentication service library with RSA key management.

## Features

- **JWT Token Management**: Create and verify access and refresh tokens
- **RSA Key Generation**: Automatic RSA key pair generation and loading
- **Configurable Expiration**: Customizable token expiration times
- **Builder Pattern**: Fluent API for service configuration
- **Structured Logging**: Built-in logging with structlog

## Quick Start

```python
from pathlib import Path
from auth_lib import JWTServiceBuilder
import uuid

# Build JWT service
jwt_service = (
    JWTServiceBuilder(None)
    .set_jwt_algorithm("RS256")
    .set_jwt_access_token_expire_minutes(15)
    .set_jwt_refresh_token_expire_days(30)
    .set_private_key_path(Path("keys/private.pem"))
    .set_public_key_path(Path("keys/public.pem"))
    .build()
)

# Create tokens
user_id = uuid.uuid4()
access_token = jwt_service.create_access_token(user_id, "user@example.com")
refresh_token = jwt_service.create_refresh_token(user_id)

# Verify token
payload = jwt_service.verify_token(access_token)
```

## Configuration

The service supports configuration via `JWTConfig`:

- `jwt_algorithm`: JWT signing algorithm (default: RS256)
- `jwt_access_token_expire_minutes`: Access token expiration (default: 15
  minutes)
- `jwt_refresh_token_expire_days`: Refresh token expiration (default: 30 days)
- `private_key_path`: Path to RSA private key file
- `public_key_path`: Path to RSA public key file

## Development

```bash
# Install dependencies
pip install -e .

# Run tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
```

## Requirements

- Python 3.8+
- cryptography
- python-jose
- pydantic
- structlog
