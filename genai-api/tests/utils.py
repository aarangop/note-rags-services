"""Test utilities and helper functions"""

from typing import Any
from unittest.mock import AsyncMock, Mock


class MockDBRow:
    """Mock database row for similarity search results"""

    def __init__(self, content: str):
        self.content = content


def create_mock_similarity_search_results(contents: list[str]) -> list[MockDBRow]:
    """Create mock similarity search results"""
    return [MockDBRow(content) for content in contents]


def create_mock_llm_response(content: str) -> Mock:
    """Create mock LLM response"""
    mock_response = Mock()
    mock_response.content = content
    return mock_response


def create_mock_prompt_response() -> Mock:
    """Create mock prompt response"""
    mock_prompt = Mock()
    mock_prompt.invoke.return_value.to_messages.return_value = []
    return mock_prompt


class MockAsyncSession(AsyncMock):
    """Mock async database session"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def create_test_query_payload(question: str = "What is the meaning of life?") -> dict[str, Any]:
    """Create a test query payload"""
    return {"question": question}


def create_expected_response(
    question: str = "What is the meaning of life?",
    answer: str = "The meaning of life is 42",
    context: list[str] | None = None,
) -> dict[str, Any]:
    """Create expected response structure"""
    if context is None:
        context = ["The meaning of life is 42"]

    return {"question": question, "answer": answer, "context": context, "db": None, "limit": 4}
