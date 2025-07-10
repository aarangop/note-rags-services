from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import config

engine = create_async_engine(config.get_db_url())

AsyncSessionLocal = async_sessionmaker(engine)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
