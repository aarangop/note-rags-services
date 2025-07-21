from pydantic import BaseModel


class BaseQuery(BaseModel):
    question: str


class Query(BaseQuery):
    pass


class QueryResponse(Query):
    response: str
    context: list[str]
    tokens: int


class ContextQuery(Query):
    limit: int = 5
