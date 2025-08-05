# Testing Utilities

This package provides comprehensive mock session utilities for testing applications that use the database package.

## Quick Start

```python
from note_rags_db.testing import create_mock_sync_session, create_mock_async_session, create_mock_db_config

# Create a mock sync session with predefined results
mock_session = create_mock_sync_session(
    first_result={"id": 1, "name": "John Doe"},
    all_results=[{"id": 1}, {"id": 2}],
    count_result=10
)

# Use it in your tests
def test_user_service():
    def get_user(session, user_id):
        return session.query(f"SELECT * FROM users WHERE id = {user_id}").first()
    
    user = get_user(mock_session, 1)
    assert user["name"] == "John Doe"
```

## Available Mock Classes

### MockSession
Mock synchronous SQLAlchemy session with:
- `add()`, `delete()`, `commit()`, `rollback()`, `close()`
- `query()`, `execute()`, `scalar()`
- Context manager support
- Query tracking in `session.queries`
- Object tracking in `session.added_objects`, `session.deleted_objects`

### MockAsyncSession
Mock asynchronous SQLAlchemy session with:
- All async equivalents of MockSession methods
- Async context manager support (`async with session:`)
- Same tracking capabilities

### MockDBConfig
Mock DBConfig that returns mock sessions:
```python
config = MockDBConfig()
sync_session = config.get_sync_session()    # Returns MockSession
async_session = config.get_async_session()  # Returns MockAsyncSession
```

## Helper Functions

### create_mock_sync_session(**kwargs)
```python
session = create_mock_sync_session(
    first_result={"id": 1, "name": "John"},
    all_results=[{"id": 1}, {"id": 2}],
    count_result=5,
    scalar_result=42,
    fetchall_results=[{"data": "value"}]
)

# Query operations will return predefined results
query = session.query("SELECT * FROM table")
assert query.first() == {"id": 1, "name": "John"}
assert query.all() == [{"id": 1}, {"id": 2}]
assert query.count() == 5
```

### create_mock_async_session(**kwargs)
Same as sync version but returns MockAsyncSession:
```python
session = create_mock_async_session(scalar_result=42)
result = await session.scalar("SELECT COUNT(*)")
assert result == 42
```

### create_mock_db_config(sync_results=None, async_results=None)
```python
config = create_mock_db_config(
    sync_results={"first_result": {"id": 1}},
    async_results={"scalar_result": 42}
)

sync_session = config.get_sync_session()
async_session = config.get_async_session()
```

## Test Examples

### Basic Sync Test
```python
def test_user_repository():
    # Setup mock session with expected data
    mock_session = create_mock_sync_session(
        first_result={"id": 1, "name": "John Doe", "email": "john@example.com"}
    )
    
    # Test your repository/service code
    def get_user_by_id(session, user_id):
        return session.query(f"SELECT * FROM users WHERE id = {user_id}").first()
    
    user = get_user_by_id(mock_session, 1)
    assert user["name"] == "John Doe"
    
    # Verify the query was executed
    assert len(mock_session.queries) == 1
    assert "SELECT * FROM users WHERE id = 1" in str(mock_session.queries[0])
```

### Basic Async Test
```python
@pytest.mark.asyncio
async def test_async_user_repository():
    mock_session = create_mock_async_session(
        scalar_result={"id": 1, "name": "John Doe"}
    )
    
    async def get_user_by_id_async(session, user_id):
        return await session.scalar(f"SELECT * FROM users WHERE id = {user_id}")
    
    user = await get_user_by_id_async(mock_session, 1)
    assert user["name"] == "John Doe"
```

### Transaction Testing
```python
def test_transaction_success():
    mock_session = create_mock_sync_session()
    
    with mock_session:
        mock_session.add({"name": "New User"})
        # No exception raised
    
    assert mock_session.committed
    assert mock_session.closed
    assert not mock_session.rolled_back

def test_transaction_rollback():
    mock_session = create_mock_sync_session()
    
    try:
        with mock_session:
            mock_session.add({"name": "New User"})
            raise ValueError("Something went wrong")
    except ValueError:
        pass
    
    assert not mock_session.committed
    assert mock_session.rolled_back
    assert mock_session.closed
```

### Testing with Dependency Injection
```python
class UserService:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_user(self, user_id):
        with self.db_config.get_sync_session() as session:
            return session.query(f"SELECT * FROM users WHERE id = {user_id}").first()

def test_user_service():
    # Inject mock config
    mock_config = create_mock_db_config(
        sync_results={"first_result": {"id": 1, "name": "John"}}
    )
    
    service = UserService(mock_config)
    user = service.get_user(1)
    
    assert user["name"] == "John"
```

## Advanced Usage

### Custom Result Types
```python
# Return different results for different queries
session = MockSession()
session.set_query_result("first_result", {"id": 1, "name": "John"})
session.set_query_result("all_results", [{"id": 1}, {"id": 2}, {"id": 3}])
session.set_query_result("count_result", 3)

# Different query methods return appropriate results
query = session.query("SELECT * FROM users")
assert query.first() == {"id": 1, "name": "John"}
assert len(query.all()) == 3
assert query.count() == 3
```

### Query Inspection
```python
mock_session = create_mock_sync_session()

# Execute some operations
mock_session.add({"name": "John"})
mock_session.query("SELECT * FROM users").first()
mock_session.execute("UPDATE users SET active = true")

# Inspect what happened
assert len(mock_session.added_objects) == 1
assert mock_session.added_objects[0]["name"] == "John"

assert len(mock_session.queries) == 2
assert any("SELECT * FROM users" in str(q) for q in mock_session.queries)
assert any("UPDATE users" in str(q) for q in mock_session.queries)
```

This testing framework makes it easy to unit test your database-dependent code without requiring actual database connections or complex mocking setups.