from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel


class BaseQuery(BaseModel):
    question: str

class Query(BaseQuery):
    pass


class QueryConfig(BaseModel):
    db: AsyncSession
    limit: int = 4

class QueryState(BaseModel):
    question: str
    context: List[str]
    answer: str
    limit: int = 4