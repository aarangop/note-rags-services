
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.db import get_db
from app.models.query import Query
from app.services.query_service import stream_query_response


router = APIRouter(prefix="/queries")


@router.post("/")
async def new_query(query: Query, db=Depends(get_db)):
    """
    Use simple retrieval and generation LangChain app to generate response. 
    """
    response = await stream_query_response(query, db)
    return response 

