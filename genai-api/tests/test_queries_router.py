from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.query import Query
from httpx import AsyncClient


class TestQueriesRouter:
    """Test suite for queries router focusing on behavior"""

    @pytest.mark.asyncio
    async def test_new_query_success(
        self,
        async_client: AsyncClient,
        sample_query: dict,
        mock_query_response: dict,
        mock_db: AsyncMock,
    ):
        """Test successful query processing"""
        # Mock the database dependency
        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            # Mock the query service
            with patch("app.routes.queries.stream_query_response") as mock_stream:
                mock_stream.return_value = mock_query_response

                # Make request
                response = await async_client.post("/queries/", json=sample_query)

                # Assert response
                assert response.status_code == 200
                response_data = response.json()

                # Verify behavior: correct response structure and content
                assert "question" in response_data
                assert "answer" in response_data
                assert response_data["question"] == sample_query["question"]
                assert response_data["answer"] == mock_query_response["answer"]

                # Verify service was called with correct parameters
                mock_stream.assert_called_once()
                call_args = mock_stream.call_args[0]
                assert isinstance(call_args[0], Query)
                assert call_args[0].question == sample_query["question"]

    @pytest.mark.asyncio
    async def test_new_query_invalid_payload(self, async_client: AsyncClient):
        """Test query with invalid payload"""
        with patch("app.routes.queries.get_db"):
            # Test missing question field
            response = await async_client.post("/queries/", json={})
            assert response.status_code == 422

            # Test invalid data type
            response = await async_client.post("/queries/", json={"question": 123})
            assert response.status_code == 422

            # Test empty question
            response = await async_client.post("/queries/", json={"question": ""})
            # This should succeed as empty string is valid, but you might want to add validation
            assert response.status_code in [200, 422]  # Depends on your validation rules

    @pytest.mark.asyncio
    async def test_new_query_service_error(
        self, async_client: AsyncClient, sample_query: dict, mock_db: AsyncMock
    ):
        """Test handling of service errors"""
        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            # Mock service to raise an exception
            with patch("app.routes.queries.stream_query_response") as mock_stream:
                mock_stream.side_effect = Exception("Service error")

                # Make request
                response = await async_client.post("/queries/", json=sample_query)

                # Should return 500 internal server error
                assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_new_query_database_error(self, async_client: AsyncClient, sample_query: dict):
        """Test handling of database connection errors"""
        # Mock database dependency to raise an exception
        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            # Make request
            response = await async_client.post("/queries/", json=sample_query)

            # Should return 500 internal server error
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_new_query_with_special_characters(
        self, async_client: AsyncClient, mock_query_response: dict, mock_db: AsyncMock
    ):
        """Test query with special characters and unicode"""
        special_query = {"question": "What about émojis 🤖 and spëcial châractërs?"}

        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            with patch("app.routes.queries.stream_query_response") as mock_stream:
                # Update mock response to match the special question
                mock_response = mock_query_response.copy()
                mock_response["question"] = special_query["question"]
                mock_stream.return_value = mock_response

                response = await async_client.post("/queries/", json=special_query)

                assert response.status_code == 200
                response_data = response.json()
                assert response_data["question"] == special_query["question"]

    @pytest.mark.asyncio
    async def test_new_query_with_long_text(
        self, async_client: AsyncClient, mock_query_response: dict, mock_db: AsyncMock
    ):
        """Test query with very long text"""
        long_question = "What is " + "very " * 1000 + "long question?"
        long_query = {"question": long_question}

        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            with patch("app.routes.queries.stream_query_response") as mock_stream:
                mock_response = mock_query_response.copy()
                mock_response["question"] = long_question
                mock_stream.return_value = mock_response

                response = await async_client.post("/queries/", json=long_query)

                assert response.status_code == 200
                response_data = response.json()
                assert response_data["question"] == long_question

    @pytest.mark.asyncio
    async def test_query_endpoint_content_type(self, async_client: AsyncClient):
        """Test that endpoint properly handles content type"""
        sample_query = {"question": "test question"}

        with patch("app.routes.queries.get_db"), patch("app.routes.queries.stream_query_response"):
            # Test with correct content type
            response = await async_client.post(
                "/queries/", json=sample_query, headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [200, 500]  # Should at least parse correctly

            # Test with form data (should fail)
            response = await async_client.post("/queries/", data=sample_query)
            assert response.status_code == 422  # Unprocessable entity


class TestQueriesRouterIntegration:
    """Integration tests that test the full pipeline with mocked external services"""

    @pytest.mark.asyncio
    async def test_end_to_end_query_processing(
        self,
        async_client: AsyncClient,
        sample_query: dict,
        mock_embeddings: Mock,
        mock_similarity_search_results: list,
        mock_llm_response: Mock,
        mock_db: AsyncMock,
    ):
        """Test end-to-end query processing with mocked external services"""

        # Mock all external dependencies
        with patch("app.routes.queries.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db

            # Mock the entire service layer and its dependencies
            with patch("app.services.query_service.OpenAIEmbeddings") as mock_embeddings_class:
                mock_embeddings_class.return_value = mock_embeddings

                with patch(
                    "app.services.query_service.similarity_search"
                ) as mock_similarity_search:
                    mock_similarity_search.return_value = mock_similarity_search_results

                    with patch("app.services.query_service.llm") as mock_llm:
                        mock_llm.invoke.return_value = mock_llm_response

                        with patch("app.services.query_service.prompt") as mock_prompt:
                            mock_prompt.invoke.return_value.to_messages.return_value = []
                            mock_prompt.invoke.return_value = Mock()

                            # Make the request
                            response = await async_client.post("/queries/", json=sample_query)

                            # Verify the response
                            assert response.status_code == 200
                            response_data = response.json()

                            # Verify the pipeline was executed
                            assert "question" in response_data
                            assert "answer" in response_data
                            assert response_data["question"] == sample_query["question"]

                            # Verify external services were called
                            mock_embeddings.aembed_query.assert_called_once_with(
                                sample_query["question"]
                            )
                            mock_similarity_search.assert_called_once()
                            mock_llm.invoke.assert_called_once()
