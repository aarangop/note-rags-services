"""Tests for testing utilities."""

import pytest
from note_rags_db.testing import (
    MockAsyncSession,
    MockDBConfig,
    MockSession,
    create_mock_async_session,
    create_mock_db_config,
    create_mock_sync_session,
)


class TestMockSession:
    """Test cases for MockSession."""

    def test_basic_operations(self):
        """Test basic session operations."""
        session = MockSession()

        # Test adding objects
        obj1 = {"id": 1, "name": "test"}
        session.add(obj1)
        assert obj1 in session.added_objects

        # Test deleting objects
        obj2 = {"id": 2, "name": "delete_me"}
        session.delete(obj2)
        assert obj2 in session.deleted_objects

        # Test commit/rollback
        session.commit()
        assert session.committed

        session.rollback()
        assert session.rolled_back

        # Test close
        session.close()
        assert session.closed

    def test_context_manager_success(self):
        """Test context manager with successful transaction."""
        session = MockSession()

        with session:
            session.add({"test": "data"})

        assert session.committed
        assert session.closed
        assert not session.rolled_back

    def test_context_manager_exception(self):
        """Test context manager with exception."""
        session = MockSession()

        try:
            with session:
                session.add({"test": "data"})
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert not session.committed
        assert session.rolled_back
        assert session.closed

    def test_query_operations(self):
        """Test query operations."""
        session = MockSession()
        session.set_query_result("first_result", {"id": 1, "name": "test"})
        session.set_query_result("all_results", [{"id": 1}, {"id": 2}])
        session.set_query_result("count_result", 5)

        # Test query method
        query = session.query("SELECT * FROM table")
        assert len(session.queries) == 1

        # Test query results
        assert query.first() == {"id": 1, "name": "test"}
        assert query.all() == [{"id": 1}, {"id": 2}]
        assert query.count() == 5

    def test_execute_operations(self):
        """Test execute operations."""
        session = MockSession()
        session.set_query_result("scalar_result", 42)

        session.execute("SELECT COUNT(*) FROM table")
        assert len(session.queries) == 1
        assert session.queries[0]["statement"] == "SELECT COUNT(*) FROM table"

        scalar_result = session.scalar("SELECT id FROM table WHERE id = 1")
        assert scalar_result == 42
        assert len(session.queries) == 2


class TestMockAsyncSession:
    """Test cases for MockAsyncSession."""

    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic async session operations."""
        session = MockAsyncSession()

        # Test adding objects
        obj1 = {"id": 1, "name": "test"}
        session.add(obj1)
        assert obj1 in session.added_objects

        # Test deleting objects
        obj2 = {"id": 2, "name": "delete_me"}
        session.delete(obj2)
        assert obj2 in session.deleted_objects

        # Test commit/rollback
        await session.commit()
        assert session.committed

        await session.rollback()
        assert session.rolled_back

        # Test close
        await session.close()
        assert session.closed

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """Test async context manager with successful transaction."""
        session = MockAsyncSession()

        async with session:
            session.add({"test": "data"})

        assert session.committed
        assert session.closed
        assert not session.rolled_back

    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """Test async context manager with exception."""
        session = MockAsyncSession()

        try:
            async with session:
                session.add({"test": "data"})
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert not session.committed
        assert session.rolled_back
        assert session.closed

    @pytest.mark.asyncio
    async def test_execute_operations(self):
        """Test async execute operations."""
        session = MockAsyncSession()
        session.set_query_result("scalar_result", 42)

        await session.execute("SELECT COUNT(*) FROM table")
        assert len(session.queries) == 1
        assert session.queries[0]["statement"] == "SELECT COUNT(*) FROM table"

        scalar_result = await session.scalar("SELECT id FROM table WHERE id = 1")
        assert scalar_result == 42
        assert len(session.queries) == 2


class TestMockDBConfig:
    """Test cases for MockDBConfig."""

    def test_basic_usage(self):
        """Test basic MockDBConfig usage."""
        config = MockDBConfig()

        sync_session = config.get_sync_session()
        async_session = config.get_async_session()

        assert isinstance(sync_session, MockSession)
        assert isinstance(async_session, MockAsyncSession)

        # Test URLs
        assert "postgresql+psycopg2" in config.get_sync_url()
        assert "postgresql+asyncpg" in config.get_async_url()

    def test_custom_sessions(self):
        """Test MockDBConfig with custom sessions."""
        custom_sync = MockSession()
        custom_async = MockAsyncSession()

        config = MockDBConfig(custom_sync, custom_async)

        assert config.get_sync_session() is custom_sync
        assert config.get_async_session() is custom_async


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_create_mock_sync_session(self):
        """Test create_mock_sync_session helper."""
        session = create_mock_sync_session(
            first_result={"id": 1}, all_results=[{"id": 1}, {"id": 2}], count_result=10
        )

        query = session.query("SELECT * FROM table")
        assert query.first() == {"id": 1}
        assert query.all() == [{"id": 1}, {"id": 2}]
        assert query.count() == 10

    def test_create_mock_async_session(self):
        """Test create_mock_async_session helper."""
        session = create_mock_async_session(
            scalar_result=42, fetchall_results=[{"id": 1}, {"id": 2}]
        )

        assert session._query_results["scalar_result"] == 42
        assert session._query_results["fetchall_results"] == [{"id": 1}, {"id": 2}]

    def test_create_mock_db_config(self):
        """Test create_mock_db_config helper."""
        config = create_mock_db_config(
            sync_results={"first_result": {"id": 1}}, async_results={"scalar_result": 42}
        )

        sync_session = config.get_sync_session()
        async_session = config.get_async_session()

        # Test sync session has predefined results
        query = sync_session.query("SELECT * FROM table")
        assert query.first() == {"id": 1}

        # Test async session has predefined results
        assert async_session._query_results["scalar_result"] == 42


class TestIntegrationExample:
    """Example integration tests showing how to use mock sessions."""

    def test_user_service_example(self):
        """Example test for a hypothetical user service."""
        # Create mock session with predefined results
        mock_session = create_mock_sync_session(
            first_result={"id": 1, "name": "John Doe", "email": "john@example.com"},
            all_results=[{"id": 1, "name": "John Doe"}, {"id": 2, "name": "Jane Smith"}],
            count_result=2,
        )

        # Simulate user service operations
        def get_user_by_id(session, user_id):
            query = session.query(f"SELECT * FROM users WHERE id = {user_id}")
            return query.first()

        def get_all_users(session):
            query = session.query("SELECT * FROM users")
            return query.all()

        def count_users(session):
            query = session.query("SELECT COUNT(*) FROM users")
            return query.count()

        # Test the service methods
        user = get_user_by_id(mock_session, 1)
        assert user["name"] == "John Doe"
        assert user["email"] == "john@example.com"

        all_users = get_all_users(mock_session)
        assert len(all_users) == 2
        assert all_users[0]["name"] == "John Doe"

        user_count = count_users(mock_session)
        assert user_count == 2

        # Verify queries were tracked
        assert len(mock_session.queries) == 3

    @pytest.mark.asyncio
    async def test_async_user_service_example(self):
        """Example async test for a hypothetical user service."""
        # Create mock async session with predefined results
        mock_session = create_mock_async_session(
            scalar_result={"id": 1, "name": "John Doe"},
            fetchall_results=[{"id": 1, "name": "John Doe"}, {"id": 2, "name": "Jane Smith"}],
        )

        # Simulate async user service operations
        async def get_user_by_id_async(session, user_id):
            result = await session.scalar(f"SELECT * FROM users WHERE id = {user_id}")
            return result

        async def get_all_users_async(session):
            result = await session.execute("SELECT * FROM users")
            return result.fetchall()

        # Test the async service methods
        user = await get_user_by_id_async(mock_session, 1)
        assert user["name"] == "John Doe"

        all_users = await get_all_users_async(mock_session)
        assert len(all_users) == 2

        # Verify queries were tracked
        assert len(mock_session.queries) == 2
