"""Testing utilities for database operations."""

from typing import Any


class MockSession:
    """Mock synchronous database session for testing."""

    def __init__(self):
        self.added_objects: list[Any] = []
        self.deleted_objects: list[Any] = []
        self.queries: list[dict[str, Any]] = []
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self._query_results: dict[str, Any] = {}

    def add(self, obj: Any) -> None:
        """Mock adding an object to the session."""
        self.added_objects.append(obj)

    def delete(self, obj: Any) -> None:
        """Mock deleting an object from the session."""
        self.deleted_objects.append(obj)

    def commit(self) -> None:
        """Mock committing the session."""
        self.committed = True

    def rollback(self) -> None:
        """Mock rolling back the session."""
        self.rolled_back = True

    def close(self) -> None:
        """Mock closing the session."""
        self.closed = True

    def flush(self) -> None:
        """Mock flushing the session."""

    def refresh(self, obj: Any) -> None:
        """Mock refreshing an object."""
        # Check if there's a custom refresh handler configured
        if hasattr(self, "_refresh_handler") and self._refresh_handler:
            self._refresh_handler(obj)

    def set_refresh_handler(self, handler):
        """Set a custom refresh handler for this session."""
        self._refresh_handler = handler

    def merge(self, obj: Any) -> Any:
        """Mock merging an object."""
        return obj

    def query(self, *args, **kwargs):
        """Mock query method."""
        query_info = {"args": args, "kwargs": kwargs}
        self.queries.append(query_info)
        return MockQuery(self._query_results)

    def execute(self, statement, parameters=None):
        """Mock execute method."""
        query_info = {"statement": statement, "parameters": parameters}
        self.queries.append(query_info)
        return MockResult(self._query_results)

    def scalar(self, statement, parameters=None):
        """Mock scalar method."""
        query_info = {"statement": statement, "parameters": parameters, "scalar": True}
        self.queries.append(query_info)
        return self._query_results.get("scalar_result")

    def set_query_result(self, key: str, value: Any) -> None:
        """Set a mock result for queries."""
        self._query_results[key] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class MockAsyncSession:
    """Mock asynchronous database session for testing."""

    def __init__(self):
        self.added_objects: list[Any] = []
        self.deleted_objects: list[Any] = []
        self.queries: list[dict[str, Any]] = []
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self._query_results: dict[str, Any] = {}

    def add(self, obj: Any) -> None:
        """Mock adding an object to the session."""
        self.added_objects.append(obj)

    def delete(self, obj: Any) -> None:
        """Mock deleting an object from the session."""
        self.deleted_objects.append(obj)

    async def commit(self) -> None:
        """Mock committing the session."""
        self.committed = True

    async def rollback(self) -> None:
        """Mock rolling back the session."""
        self.rolled_back = True

    async def close(self) -> None:
        """Mock closing the session."""
        self.closed = True

    async def flush(self) -> None:
        """Mock flushing the session."""

    async def refresh(self, obj: Any) -> None:
        """Mock refreshing an object."""
        # Check if there's a custom refresh handler configured
        if hasattr(self, "_refresh_handler") and self._refresh_handler:
            self._refresh_handler(obj)

    def set_refresh_handler(self, handler):
        """Set a custom refresh handler for this session."""
        self._refresh_handler = handler

    async def merge(self, obj: Any) -> Any:
        """Mock merging an object."""
        return obj

    async def execute(self, statement, parameters=None):
        """Mock execute method."""
        query_info = {"statement": statement, "parameters": parameters}
        self.queries.append(query_info)
        return MockResult(self._query_results)

    async def scalar(self, statement, parameters=None):
        """Mock scalar method."""
        query_info = {"statement": statement, "parameters": parameters, "scalar": True}
        self.queries.append(query_info)
        return self._query_results.get("scalar_result")

    def set_query_result(self, key: str, value: Any) -> None:
        """Set a mock result for queries."""
        self._query_results[key] = value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


class MockQuery:
    """Mock query object for synchronous sessions."""

    def __init__(self, results: dict[str, Any]):
        self._results = results

    def filter(self, *args, **kwargs):
        """Mock filter method."""
        return self

    def filter_by(self, **kwargs):
        """Mock filter_by method."""
        return self

    def order_by(self, *args):
        """Mock order_by method."""
        return self

    def limit(self, limit):
        """Mock limit method."""
        return self

    def offset(self, offset):
        """Mock offset method."""
        return self

    def first(self):
        """Mock first method."""
        return self._results.get("first_result")

    def all(self):
        """Mock all method."""
        return self._results.get("all_results", [])

    def one(self):
        """Mock one method."""
        result = self._results.get("one_result")
        if result is None:
            raise Exception("No result found")
        return result

    def one_or_none(self):
        """Mock one_or_none method."""
        return self._results.get("one_or_none_result")

    def count(self):
        """Mock count method."""
        return self._results.get("count_result", 0)


class MockResult:
    """Mock result object for execute methods."""

    def __init__(self, results: dict[str, Any]):
        self._results = results

    def fetchone(self):
        """Mock fetchone method."""
        return self._results.get("fetchone_result")

    def fetchall(self):
        """Mock fetchall method."""
        return self._results.get("fetchall_results", [])

    def fetchmany(self, size=None):
        """Mock fetchmany method."""
        return self._results.get("fetchmany_results", [])

    def scalar(self):
        """Mock scalar method."""
        return self._results.get("scalar_result")

    def scalars(self):
        """Mock scalars method."""
        return MockScalars(self._results.get("scalars_results", []))

    def scalar_one_or_none(self):
        """Mock scalar_one_or_none method."""
        scalars = self.scalars()
        return scalars.one_or_none()


class MockScalars:
    """Mock scalars result object."""

    def __init__(self, results: list[Any]):
        self._results = results

    def first(self):
        """Mock first method."""
        return self._results[0] if self._results else None

    def all(self):
        """Mock all method."""
        return self._results

    def one(self):
        """Mock one method."""
        if len(self._results) != 1:
            raise Exception("Expected exactly one result")
        return self._results[0]

    def one_or_none(self):
        """Mock one_or_none method."""
        if len(self._results) > 1:
            raise Exception("Expected at most one result")
        return self._results[0] if self._results else None


class MockDBConfig:
    """Mock DBConfig for testing that returns mock sessions."""

    def __init__(
        self,
        mock_sync_session: MockSession | None = None,
        mock_async_session: MockAsyncSession | None = None,
    ):
        self._mock_sync_session = mock_sync_session or MockSession()
        self._mock_async_session = mock_async_session or MockAsyncSession()

    def get_sync_session(self) -> MockSession:
        """Return a mock synchronous session."""
        return self._mock_sync_session

    def get_async_session(self) -> MockAsyncSession:
        """Return a mock asynchronous session."""
        return self._mock_async_session

    def get_sync_url(self) -> str:
        """Return a mock sync URL."""
        return "postgresql+psycopg2://testuser:testpass@localhost:5432/testdb"

    def get_async_url(self) -> str:
        """Return a mock async URL."""
        return "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb"


def create_mock_sync_session(**kwargs) -> MockSession:
    """
    Create a mock synchronous session with optional predefined results.

    Args:
        **kwargs: Predefined results for queries (e.g., first_result=obj, all_results=[...])

    Returns:
        MockSession instance
    """
    session = MockSession()
    for key, value in kwargs.items():
        session.set_query_result(key, value)
    return session


def create_mock_async_session(**kwargs) -> MockAsyncSession:
    """
    Create a mock asynchronous session with optional predefined results.

    Args:
        **kwargs: Predefined results for queries (e.g., first_result=obj, all_results=[...])

    Returns:
        MockAsyncSession instance
    """
    session = MockAsyncSession()
    for key, value in kwargs.items():
        session.set_query_result(key, value)
    return session


def create_mock_db_config(
    sync_results: dict[str, Any] | None = None, async_results: dict[str, Any] | None = None
) -> MockDBConfig:
    """
    Create a mock DBConfig with predefined session results.

    Args:
        sync_results: Results to return for synchronous session queries
        async_results: Results to return for asynchronous session queries

    Returns:
        MockDBConfig instance
    """
    sync_session = create_mock_sync_session(**(sync_results or {}))
    async_session = create_mock_async_session(**(async_results or {}))
    return MockDBConfig(sync_session, async_session)
