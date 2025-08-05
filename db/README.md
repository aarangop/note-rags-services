# Note RAGs Database Package

A robust, dialect-agnostic database configuration and session management package for SQL databases, with comprehensive testing utilities.

## Features

- **Flexible Database Configuration** - Support for PostgreSQL, MySQL, SQLite, Oracle, and SQL Server
- **Automatic Driver Selection** - Intelligent sync/async driver selection based on database dialect
- **Session Management** - Easy creation of both synchronous and asynchronous database sessions
- **URL Generation** - Robust connection string generation with proper encoding
- **Comprehensive Testing** - Mock sessions and utilities for testing database-dependent code
- **Type Safe** - Full type hints and validation using Pydantic

## Installation

```bash
pip install note-rags-db
```

## Quick Start

### Basic Configuration

```python
from note_rags_db import DBConfig
from pydantic import SecretStr

# Configure your database
config = DBConfig(
    db_host="localhost",
    db_port=5432,
    db_user="myuser",
    db_password=SecretStr("mypassword"),
    db_name="mydatabase",
    db_dialect="postgresql"
)

# Get connection URLs
sync_url = config.get_sync_url()
# postgresql+psycopg2://myuser:mypassword@localhost:5432/mydatabase

async_url = config.get_async_url() 
# postgresql+asyncpg://myuser:mypassword@localhost:5432/mydatabase
```

### Session Management

```python
# Get database sessions
sync_session = config.get_sync_session()
async_session = config.get_async_session()

# Use with context managers
with config.get_sync_session() as session:
    result = session.execute("SELECT * FROM users")
    users = result.fetchall()

# Async usage
async with config.get_async_session() as session:
    result = await session.execute("SELECT * FROM users")
    users = result.fetchall()
```

## Configuration Options

### Environment Variables

The `DBConfig` class automatically reads from environment variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=myuser
export DB_PASSWORD=mypassword
export DB_NAME=mydatabase
export DB_DIALECT=postgresql
export DB_DRIVER=psycopg2  # Optional: override default driver
```

### Configuration Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `db_host` | `str` | Database host |  |
| `db_port` | `int \| None` | Database port | L |
| `db_user` | `str` | Database username |  |
| `db_password` | `SecretStr` | Database password |  |
| `db_name` | `str` | Database name |  |
| `db_dialect` | `str` | Database dialect |  |
| `db_driver` | `str \| None` | Database driver override | L |
| `db_url` | `str \| None` | Complete URL override | L |

### Supported Dialects

| Dialect | Sync Driver | Async Driver |
|---------|-------------|--------------|
| `postgresql` | `psycopg2` | `asyncpg` |
| `mysql` | `pymysql` | `aiomysql` |
| `sqlite` | built-in | `aiosqlite` |
| `oracle` | `cx_oracle` | - |
| `mssql` | `pyodbc` | - |

## Advanced Usage

### Custom Driver Selection

```python
config = DBConfig(
    db_host="localhost",
    db_user="user",
    db_password=SecretStr("pass"),
    db_name="db",
    db_dialect="postgresql",
    db_driver="pg8000"  # Use pg8000 instead of psycopg2
)
```

### Complete URL Override

```python
config = DBConfig(
    db_host="dummy",  # Required but ignored
    db_user="dummy",  # Required but ignored
    db_password=SecretStr("dummy"),  # Required but ignored
    db_name="dummy",  # Required but ignored
    db_dialect="postgresql",  # Required but ignored
    db_url="postgresql://user:pass@custom-host:5432/custom-db"
)
```

### SQLite Configuration

```python
config = DBConfig(
    db_host="localhost",  # Ignored for SQLite
    db_user="dummy",      # Ignored for SQLite
    db_password=SecretStr("dummy"),  # Ignored for SQLite
    db_name="./database.db",  # File path
    db_dialect="sqlite"
)

sync_url = config.get_sync_url()   # sqlite:///./database.db
async_url = config.get_async_url() # sqlite+aiosqlite:///./database.db
```

## Database Models

Use the provided `Base` class for your SQLAlchemy models:

```python
from note_rags_db import Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))
```

## Testing

The package includes comprehensive testing utilities for mocking database sessions:

```python
from note_rags_db.testing import create_mock_sync_session, create_mock_db_config

# Create mock session with predefined results
mock_session = create_mock_sync_session(
    first_result={"id": 1, "name": "John Doe"},
    all_results=[{"id": 1}, {"id": 2}],
    count_result=10
)

# Test your database code
def get_user_by_id(session, user_id):
    return session.query(f"SELECT * FROM users WHERE id = {user_id}").first()

user = get_user_by_id(mock_session, 1)
assert user["name"] == "John Doe"

# Mock the entire config for dependency injection
mock_config = create_mock_db_config(
    sync_results={"first_result": {"id": 1, "name": "John"}}
)

class UserService:
    def __init__(self, db_config):
        self.db_config = db_config
    
    def get_user(self, user_id):
        with self.db_config.get_sync_session() as session:
            return session.query(f"SELECT * FROM users WHERE id = {user_id}").first()

# Test with mock config
service = UserService(mock_config)
user = service.get_user(1)
assert user["name"] == "John"
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Error Handling and Validation

The package includes robust validation:

```python
from pydantic import ValidationError

try:
    config = DBConfig(
        db_host="localhost",
        db_port=99999,  # Invalid port
        db_user="user",
        db_password=SecretStr("pass"),
        db_name="db",
        db_dialect="unsupported"  # Invalid dialect
    )
except ValidationError as e:
    print(e)
    # Port must be between 1 and 65535
    # Unsupported dialect: unsupported. Supported: ['postgresql', 'mysql', 'sqlite', 'oracle', 'mssql']
```

## Migration Support

The package works seamlessly with Alembic for database migrations:

```python
# alembic/env.py
from note_rags_db import DBConfig, Base
from pydantic import SecretStr

config = DBConfig(
    db_host="localhost",
    db_port=5432,
    db_user="user",
    db_password=SecretStr("password"),
    db_name="database",
    db_dialect="postgresql"
)

# Use the sync URL for Alembic
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", config.get_sync_url())
```

## Connection Pooling

For production use, you may want to configure connection pooling:

```python
from note_rags_db import create_db_engine
from sqlalchemy import create_engine

config = DBConfig(...)

# Create engine with custom pool settings
engine = create_engine(
    config.get_sync_url(),
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

## Async Usage with FastAPI

Perfect integration with FastAPI applications:

```python
from fastapi import FastAPI, Depends
from note_rags_db import DBConfig
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()
config = DBConfig()  # Reads from environment

async def get_db_session() -> AsyncSession:
    async with config.get_async_session() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute("SELECT * FROM users WHERE id = :id", {"id": user_id})
    return result.fetchone()
```

## Security Features

- **Password Protection**: Uses Pydantic's `SecretStr` to prevent password leakage in logs
- **URL Encoding**: Automatic encoding of special characters in connection strings
- **Validation**: Input validation prevents common configuration errors

## Performance Considerations

- **Lazy Loading**: Database connections are only created when sessions are requested
- **Driver Selection**: Automatic selection of the most appropriate driver for each dialect
- **Connection Reuse**: Sessions can be reused within the same context

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v1.0.0
- Initial release
- Support for PostgreSQL, MySQL, SQLite, Oracle, and SQL Server
- Synchronous and asynchronous session management
- Comprehensive testing utilities
- Full type safety with Pydantic validation

## Support

- **Documentation**: See [TESTING.md](TESTING.md) for testing utilities
- **Issues**: Report bugs and feature requests on GitHub
- **Examples**: Check the `tests/` directory for usage examples