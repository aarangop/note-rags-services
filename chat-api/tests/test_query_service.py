from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.query import Query
from app.services.query_service import QueryState, answer_query, generate, retrieve

from tests.utils import (
    MockAsyncSession,
    create_mock_llm_response,
    create_mock_similarity_search_results,
)


class TestQueryService:
    """Test the query service behavior without testing implementation details"""

    @pytest.mark.asyncio
    async def test_stream_query_response_returns_complete_result(self):
        """Test that stream_query_response returns a complete response structure"""
        # Arrange
        query = Query(question="What is Python?")
        mock_db = MockAsyncSession()

        expected_answer = "Python is a programming language"

        # Mock all external dependencies
        with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
            mock_embeddings = Mock()
            mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_embeddings_class.return_value = mock_embeddings

            with patch("app.services.query_service.similarity_search") as mock_similarity_search:
                mock_results = create_mock_similarity_search_results(
                    [
                        "Python is a high-level programming language",
                        "Python was created by Guido van Rossum",
                    ]
                )
                mock_similarity_search.return_value = mock_results

                with patch("app.services.query_service.llm") as mock_llm:
                    mock_llm.invoke.return_value = create_mock_llm_response(expected_answer)

                    with patch("app.services.query_service.prompt") as mock_prompt:
                        mock_prompt.invoke.return_value = Mock()

                        # Act
                        result = await answer_query(query, mock_db)

                        # Assert
                        assert isinstance(result, dict)
                        assert "question" in result
                        assert "answer" in result
                        assert "context" in result
                        assert result["question"] == query.question
                        assert result["answer"] == expected_answer
                        assert isinstance(result["context"], list)

    @pytest.mark.asyncio
    async def test_retrieve_function_behavior(self):
        """Test the retrieve function returns context from similarity search"""
        # Arrange
        state = QueryState(question="What is machine learning?", db=MockAsyncSession(), limit=3)

        expected_contents = [
            "Machine learning is a subset of AI",
            "ML algorithms learn from data",
            "Deep learning is a type of ML",
        ]

        # Mock dependencies
        with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
            mock_embeddings = Mock()
            mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_embeddings_class.return_value = mock_embeddings

            with patch("app.services.query_service.similarity_search") as mock_similarity_search:
                mock_results = create_mock_similarity_search_results(expected_contents)
                mock_similarity_search.return_value = mock_results

                # Act
                result = await retrieve(state)

                # Assert
                assert "context" in result
                assert isinstance(result["context"], list)
                assert len(result["context"]) == len(expected_contents)
                assert result["context"] == expected_contents

                # Verify embeddings were created for the question
                mock_embeddings.aembed_query.assert_called_once_with(state.question)

                # Verify similarity search was called with correct parameters
                mock_similarity_search.assert_called_once()
                call_args = mock_similarity_search.call_args[0]
                assert call_args[0] == state.db  # database session
                assert call_args[2] == state.limit  # limit parameter

    @pytest.mark.asyncio
    async def test_generate_function_behavior(self):
        """Test the generate function produces an answer from context"""
        # Arrange
        context_docs = [
            "Artificial Intelligence is the simulation of human intelligence",
            "AI systems can perform tasks that typically require human intelligence",
        ]

        state = QueryState(question="What is AI?", db=MockAsyncSession(), context=context_docs)

        expected_answer = "AI is the simulation of human intelligence in machines"

        # Mock dependencies
        with patch("app.services.query_service.prompt") as mock_prompt:
            mock_prompt.invoke.return_value = Mock()

            with patch("app.services.query_service.llm") as mock_llm:
                mock_llm.invoke.return_value = create_mock_llm_response(expected_answer)

                # Act
                result = await generate(state)

                # Assert
                assert "answer" in result
                assert result["answer"] == expected_answer

                # Verify prompt was invoked with question and context
                mock_prompt.invoke.assert_called_once()
                prompt_call_args = mock_prompt.invoke.call_args[0][0]
                assert prompt_call_args["question"] == state.question
                assert prompt_call_args["context"] == "\n\n".join(context_docs)

                # Verify LLM was invoked
                mock_llm.invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_service_handles_empty_context(self):
        """Test behavior when no context is found"""
        query = Query(question="Very obscure question with no results")
        mock_db = MockAsyncSession()

        expected_answer = "I don't have enough information to answer that question"

        with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
            mock_embeddings = Mock()
            mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_embeddings_class.return_value = mock_embeddings

            with patch("app.services.query_service.similarity_search") as mock_similarity_search:
                # Return empty results
                mock_similarity_search.return_value = []

                with patch("app.services.query_service.llm") as mock_llm:
                    mock_llm.invoke.return_value = create_mock_llm_response(expected_answer)

                    with patch("app.services.query_service.prompt") as mock_prompt:
                        mock_prompt.invoke.return_value = Mock()

                        # Act
                        result = await answer_query(query, mock_db)

                        # Assert
                        assert result["context"] == []
                        assert result["answer"] == expected_answer

    @pytest.mark.asyncio
    async def test_query_service_handles_database_errors(self):
        """Test how the service handles database connection errors"""
        query = Query(question="Test question")
        mock_db = MockAsyncSession()

        with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
            mock_embeddings = Mock()
            mock_embeddings.aembed_query = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_embeddings_class.return_value = mock_embeddings

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await answer_query(query, mock_db)

            assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_service_handles_llm_errors(self):
        """Test how the service handles LLM API errors"""
        query = Query(question="Test question")
        mock_db = MockAsyncSession()

        with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
            mock_embeddings = Mock()
            mock_embeddings.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_embeddings_class.return_value = mock_embeddings

            with patch("app.services.query_service.similarity_search") as mock_similarity_search:
                mock_results = create_mock_similarity_search_results(["Some context"])
                mock_similarity_search.return_value = mock_results

                with patch("app.services.query_service.llm") as mock_llm:
                    mock_llm.invoke.side_effect = Exception("LLM API error")

                    with patch("app.services.query_service.prompt") as mock_prompt:
                        mock_prompt.invoke.return_value = Mock()

                        # Act & Assert
                        with pytest.raises(Exception) as exc_info:
                            await answer_query(query, mock_db)

                        assert "LLM API error" in str(exc_info.value)
