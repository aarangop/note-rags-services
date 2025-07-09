from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chats_router, queries_router

app = FastAPI(
    title="Chat API",
    description="Chat microservice for RAG-powered chatbot",
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

app.include_router(chats_router)
app.include_router(queries_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "chat-api"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Chat API is running", "version": "0.1.0"}
