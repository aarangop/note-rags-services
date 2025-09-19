# Note RAGs Database Package

Database configuration, session management, and migration utilities for the Note RAGs application.

## Features

- Database configuration with multiple dialect support
- Synchronous and asynchronous session management
- Alembic integration for database migrations
- PGVector extension setup
- CLI tools for database operations

## CLI Commands

```bash
# Initialize database and install PGVector extension
note-rags-db init --database-url postgresql://user:pass@host:5432/dbname

# Run database migrations to latest schema
note-rags-db upgrade --database-url postgresql://user:pass@host:5432/dbname

# Reset database (drop all tables and migration history)
note-rags-db reset --database-url postgresql://user:pass@host:5432/dbname

# Show available commands
note-rags-db --help
```

## Installation

This package is part of the Note RAGs workspace and is installed automatically with workspace dependencies.