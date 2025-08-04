from note_rags_db.config import DBConfig
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Config, get_config


def get_db_config(config: Config):
    return DBConfig(
        db_dialect="postgres",
        db_driver="psycopg2",
        db_url=config.db_url,
        db_name=config.db_name,
        db_user=config.db_user,
        db_password=config.db_password,
    )


db_config = get_db_config(get_config())
engine = create_async_engine(db_config.get_db_url())

AsyncSessionLocal = async_sessionmaker(engine)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
