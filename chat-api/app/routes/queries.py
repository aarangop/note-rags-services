from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.db import get_db
from app.models.query import Query, QueryResponse
from app.services.query_service import answer_query, stream_query_response

router = APIRouter(prefix="/queries")


@router.post("/", response_model=QueryResponse)
async def new_query(query: Query, db=Depends(get_db)):
    """
    Use simple retrieval and generation LangChain app to generate response.
    """
    response = await answer_query(query, db)
    return response


@router.post("/streams")
async def new_query_stream(query: Query, db=Depends(get_db)):
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
