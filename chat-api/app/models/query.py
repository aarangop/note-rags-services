from dataclasses import dataclass
from typing import List

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


class BaseQuery(BaseModel):
    question: str


class Query(BaseQuery):
    pass


