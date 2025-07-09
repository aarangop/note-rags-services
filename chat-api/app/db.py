from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app import config

engine = create_async_engine(config.get_db_url())

AsyncSessionLocal = async_sessionmaker()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session