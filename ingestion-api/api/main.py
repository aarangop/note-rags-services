from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db import Base, async_engine
from api.logging_config import configure_logging, get_logger
from api.routes import file_event_router, health_router

# Configure structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with async_engine.begin() as conn:
        logger.debug("Creating database tables", operation="database_init")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully", operation="database_init")

    yield

    await async_engine.dispose()
    logger.info("Database connection disposed", operation="database_cleanup")


app = FastAPI(
    title="Ingestion API",
    description="Data ingestion microservice for RAG-powered chatbot",
    version="0.1.0",
    lifespan=lifespan,
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
