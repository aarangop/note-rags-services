import json
from dataclasses import dataclass, field
from typing import TypedDict

from langchain import hub
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.models.query import Query
from app.services.context import similarity_search
from app.services.embeddings import get_embeddings

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
    context: list[str] = field(default_factory=list)
    answer: str = ""
    limit: int = 4


async def retrieve(state: QueryState) -> dict[str, list[str]]:
    db = state.db

    limit = state.limit

    query_embedding = await get_embeddings(state.question, config=get_config())
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


async def answer_query(query: Query, db: AsyncSession):
    result = await rag_pipeline.ainvoke(
        QueryState(
            question=query.question,
            db=db,
        )
    )
    return result


async def stream_query_response(query: Query, db: AsyncSession):
    """
    Stream the query response using the existing LangGraph workflow.
    Formats the output as Server-Sent Events (SSE).
    """
    try:
        async for chunk in rag_pipeline.astream(QueryState(question=query.question, db=db)):
            # Format each chunk as SSE data
            if chunk:
                # Determine the type of chunk based on its content
                chunk_data = {}

                if "retrieve" in chunk:
                    # This is from the retrieve node
                    retrieve_data = chunk["retrieve"]
                    if "context" in retrieve_data:
                        chunk_data = {
                            "type": "context",
                            "step": "retrieve",
                            "context": retrieve_data["context"],
                        }
                elif "generate" in chunk:
                    # This is from the generate node
                    generate_data = chunk["generate"]
                    if "answer" in generate_data:
                        chunk_data = {
                            "type": "answer",
                            "step": "generate",
                            "content": generate_data["answer"],
                        }
                else:
                    # Generic chunk data
                    chunk_data = {"type": "chunk", "data": chunk}

                yield f"data: {json.dumps(chunk_data)}\n\n"

        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    except Exception as e:
        # Send error in SSE format
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
