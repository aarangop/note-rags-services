# Test Suite for Queries Router

This test suite focuses on testing the behavior of the queries router and
related services, rather than implementation details.

## Test Structure

### `test_queries_router.py`

- **Unit Tests**: Test the router endpoint behavior with mocked dependencies
- **Integration Tests**: Test the full pipeline with mocked external services
  (LLM, embeddings)

### `test_query_service.py`

- **Service Layer Tests**: Test the query service behavior independently
- **Error Handling Tests**: Test how the service handles various error
  conditions

### `conftest.py`

- Contains shared fixtures for all tests
- Provides mock objects for common dependencies

### `utils.py`

- Helper functions for creating test data and mock objects
- Utility functions to reduce test code duplication

## Key Testing Principles

1. **Behavior Over Implementation**: Tests focus on what the system does, not
   how it does it
2. **Mock External Dependencies**: All external API calls (OpenAI, database) are
   mocked
3. **Test Error Scenarios**: Comprehensive error handling tests
4. **Fast and Reliable**: Tests run quickly and don't depend on external
   services

## Running Tests

### Install Test Dependencies

```bash
# Using uv (recommended)
uv sync --group test

# Or using pip
pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/test_queries_router.py

# Run specific test
pytest tests/test_queries_router.py::TestQueriesRouter::test_new_query_success
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

## Test Coverage

The test suite covers:

- ✅ Successful query processing
- ✅ Invalid request payloads
- ✅ Service layer errors
- ✅ Database connection errors
- ✅ LLM API errors
- ✅ Special characters and unicode handling
- ✅ Long text queries
- ✅ Empty context scenarios
- ✅ Content type validation
- ✅ End-to-end pipeline behavior

## Mocking Strategy

### External Services Mocked:

- **OpenAI Embeddings API**: Mock embedding generation
- **OpenAI LLM API**: Mock text generation
- **Database Queries**: Mock similarity search results
- **LangChain Components**: Mock prompt templates and pipeline

### What's NOT Mocked:

- **FastAPI Framework**: Use real FastAPI test client
- **Pydantic Models**: Use real validation logic
- **Router Logic**: Test actual router behavior

## Adding New Tests

When adding new tests:

1. **Follow Naming Conventions**: Use descriptive test names that explain the
   scenario
2. **Use Existing Fixtures**: Leverage shared fixtures from `conftest.py`
3. **Mock External Dependencies**: Don't make real API calls
4. **Test Both Success and Failure**: Include error scenarios
5. **Focus on Behavior**: Test what the system should do, not how it does it

## Example Test Pattern

```python
@pytest.mark.asyncio
async def test_specific_behavior(self, async_client, mock_dependencies):
    """Test description explaining the scenario"""
    # Arrange: Set up test data and mocks
    test_data = {...}
    with patch("module.dependency") as mock_dep:
        mock_dep.return_value = expected_result

        # Act: Execute the behavior being tested
        response = await async_client.post("/endpoint", json=test_data)

        # Assert: Verify the expected behavior
        assert response.status_code == 200
        assert response.json()["field"] == expected_value
        mock_dep.assert_called_once_with(expected_args)
```
