import os
from pathlib import Path
import pytest
from app.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

test_env_path = Path(__file__).parent.parent / ".env.text"

@pytest.fixture(scope="session")
def config() -> Config:
    return Config(env_file="../../.env.test")

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine() 

@pytest.fixture(scope="session")
async def db_session(test_engine):
    pass


if __name__ == "__main__":
    print(os.getcwd())