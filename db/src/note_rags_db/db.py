from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):
    """Create a synchronous database engine from a connection URL."""
    return create_engine(database_url)


def create_async_db_engine(database_url: str):
    """Create an asynchronous database engine from a connection URL."""
    return create_async_engine(database_url)


def create_session_factory(engine):
    """Create a session factory for synchronous database operations."""
    return sessionmaker(bind=engine, class_=Session)


def create_async_session_factory(async_engine):
    """Create a session factory for asynchronous database operations."""
    return async_sessionmaker(bind=async_engine, class_=AsyncSession)
