from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from note_rags_db.config import config


class Base(DeclarativeBase):
    pass


engine = create_engine(config.get_url())
