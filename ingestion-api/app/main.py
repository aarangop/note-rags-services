from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import configure_logging, get_logger
from app.routes import file_event_router, health_router

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


app = FastAPI(
    title="Ingestion API",
    description="Data ingestion microservice for RAG-powered chatbot",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed", endpoint="/", method="GET")
    return {"message": "Ingestion API is running", "version": "0.1.0"}


app.include_router(file_event_router)
app.include_router(health_router)
