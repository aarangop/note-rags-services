# Auth Library Tests

This directory contains comprehensive unit tests for the Auth Library
components.

## Test Structure

- `conftest.py` - Shared test fixtures and utilities
- `test_jwt_service_builder.py` - Tests for the JWTServiceBuilder class
- `test_jwt_service.py` - Tests for the JWTService class

## Running Tests

From the auth-lib directory:

```bash
# Install test dependencies
uv add --optional test pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_jwt_service.py

# Run tests with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_create_access_token"
```

## Test Coverage

The test suite covers:

### JWTServiceBuilder Tests

- Default configuration handling
- Method chaining functionality
- Configuration validation
- Service creation with proper parameters
- Error handling for missing key paths

### JWTService Tests

- Key initialization (existing keys and key generation)
- Access token creation and verification
- Refresh token creation and verification
- Token expiration handling
- Additional claims support
- Error handling for missing keys
- Different JWT algorithms support
- Token uniqueness (JTI)
- Edge cases and error conditions

## Test Fixtures

The test suite includes several helpful fixtures:

- `temp_dir` - Temporary directory for test files
- `test_rsa_keys` - Generated RSA key pair for testing
- `key_files` - Temporary key files on disk
- `test_user_data` - Sample user data for token creation
- `sample_claims` - Additional claims for testing

## Notes

- Tests use temporary directories and files to avoid affecting the file system
- RSA keys are generated on-the-fly for testing purposes
- All tests are isolated and can run independently
- Tests cover both happy path and error scenarios
