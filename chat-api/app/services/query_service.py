
from typing import Dict, List, TypedDict, cast
from sqlalchemy import select, func
from langchain import hub
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import OpenAIEmbeddings
from app.models.query import Query, QueryConfig, QueryState
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig


from app.services.context import similarity_search

prompt = hub.pull("rlm/rag-prompt")

def get_prompt(query: Query, context: str):
    return prompt.invoke(
        {
            "context": context,
            "question": query.question
        }
    ).to_messages()

class ConfigurableDict(TypedDict):
    db: AsyncSession

def get_db_from_config(config: RunnableConfig) -> AsyncSession:
    """Type-safe helper to extract database from config."""
    configurable = config.get("configurable")
    if not configurable:
        raise ValueError("No configurable section found in RunnableConfig")
    
    db = configurable.get("db")
    if not db:
        raise ValueError("Database session not found in configurable")
    
    return db

async def retrieve(state: QueryState, config: RunnableConfig) -> Dict[str, List[str]]:
    configurable_raw = config.get("configurable", {})
    configurable: ConfigurableDict = cast(ConfigurableDict, configurable_raw)
    db = configurable["db"]

    limit = state.limit

    embeddings = OpenAIEmbeddings() 
    query_embedding = await embeddings.aembed_query(state.question)
    chunks = await similarity_search(db, query_embedding, limit)

    return {"context": [row.content for row in chunks] }

async def generate(state: QueryState, config: QueryConfig):
    return {"answer": "Dunno!"}

workflow = StateGraph(QueryState)
workflow.add_node("retrieve", retrieve)
async def stream_query_response(query: Query, db: AsyncSession):
    response = "Not implemented"

    for c in response:
        yield bytes(c, encoding='utf-8')

