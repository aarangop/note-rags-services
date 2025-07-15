from unittest.mock import AsyncMock, Mock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def mock_app():
    """Create test FastAPI app"""
    return app


@pytest.fixture
async def async_client(mock_app):
    """Async HTTP client for testing"""
    async with AsyncClient(transport=ASGITransport(app=mock_app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_query_response():
    """Mock response from query service"""
    return {
        "question": "What is the meaning of life?",
        "context": ["The meaning of life is 42", "According to Douglas Adams"],
        "answer": "The meaning of life is 42, according to Douglas Adams in 'The Hitchhiker's Guide to the Galaxy'",
        "db": None,
        "limit": 4,
    }


@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return {"question": "What is the meaning of life?"}


@pytest.fixture
def mock_embeddings():
    """Mock OpenAI embeddings"""
    mock = Mock()
    mock.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return mock


@pytest.fixture
def mock_similarity_search_results():
    """Mock similarity search results"""
    mock_result = Mock()
    mock_result.content = "The meaning of life is 42"
    return [mock_result]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response"""
    mock_response = Mock()
    mock_response.content = "The meaning of life is 42, according to Douglas Adams"
    return mock_response
