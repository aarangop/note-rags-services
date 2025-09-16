from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from note_rags_db import get_async_db_session

from app.models.query import Query, QueryResponse
from app.services.query_service import answer_query, stream_query_response

router = APIRouter(prefix="/queries")


@router.post("/", response_model=QueryResponse)
async def new_query(query: Query, db=Depends(get_async_db_session)):
    """
    Use simple retrieval and generation LangChain app to generate response.
    """
    response = await answer_query(query, db)
    return response


@router.post("/streams")
async def new_query_stream(query: Query, db=Depends(get_async_db_session)):
    """
    Stream the query response using Server-Sent Events (SSE).
    Returns real-time updates including context retrieval and response generation.
    """
    return StreamingResponse(
        stream_query_response(query, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )
