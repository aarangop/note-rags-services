from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import notes_router
from app.routes.health import router as health_router

app = FastAPI(
    title="Notes API",
    description="Notes microservice for managing notes",
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

app.include_router(health_router, prefix="/health")
app.include_router(notes_router, prefix="/notes")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Notes API is running", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8002)
