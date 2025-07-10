from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):
    """Create a database engine from a connection URL."""
    return create_engine(database_url)
