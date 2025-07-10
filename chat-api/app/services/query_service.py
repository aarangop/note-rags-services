from dataclasses import dataclass, field
from typing import Dict, List, TypedDict, cast

from langchain import hub
from langchain_core.runnables import RunnableConfig
from langchain_openai import OpenAIEmbeddings
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query import Query
from app.services.context import similarity_search

prompt = hub.pull("rlm/rag-prompt")


llm = init_chat_model(model="gpt-4.1-mini-2025-04-14", model_provider="openai")

def get_prompt(query: Query, context: str):
    return prompt.invoke({"context": context, "question": query.question}).to_messages()


class ConfigurableDict(TypedDict):
    db: AsyncSession

@dataclass
class QueryConfig:
    db: AsyncSession
    limit: int = 4


@dataclass
class QueryState:
    question: str
    db: AsyncSession
    context: List[str] = field(default_factory=list)
    answer: str = ""
    limit: int = 4

async def retrieve(state: QueryState) -> Dict[str, List[str]]:
    db = state.db

    limit = state.limit

    embeddings = OpenAIEmbeddings()
    query_embedding = await embeddings.aembed_query(state.question)
    chunks = await similarity_search(db, query_embedding, limit)
    context = [row.content for row in chunks]

    return {"context": context}

async def generate(state: QueryState):

    docs_content = "\n\n".join(doc for doc in state.context)
    messages = prompt.invoke({"question": state.question, "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content}


# Build pipeline once
workflow = StateGraph(QueryState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_edge("retrieve", "generate")
workflow.set_entry_point("retrieve")
workflow.set_finish_point("generate")

rag_pipeline = workflow.compile()


async def stream_query_response(query: Query, db: AsyncSession):
    result = await rag_pipeline.ainvoke(QueryState(
        question=query.question,
        db=db,
    )) 
    return result
