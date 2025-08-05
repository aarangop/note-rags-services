from note_rags_db.config import DBConfig

from app.config import get_config

# Global variable for lazy initialization
_db_config = None


def get_db_config() -> DBConfig:
    """Get or create the database configuration."""
    global _db_config
    if _db_config is None:
        config = get_config()

        # Use full URL if provided, otherwise construct from components
        if config.db_full_url:
            _db_config = DBConfig(db_url=config.db_full_url)
        else:
            # Use individual components
            _db_config = DBConfig(
                db_host=config.db_host,
                db_port=config.db_port,
                db_user=config.db_user,
                db_password=config.db_password,
                db_name=config.db_name,
                db_dialect="postgresql",
            )
    return _db_config


async def get_db():
    """Get database session for dependency injection."""
    db_config = get_db_config()
    async with db_config.get_async_session() as session:
        yield session
