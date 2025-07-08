# Ingestion API Microservice

This is the data ingestion API microservice for the RAG-powered chatbot system.
It handles file change events, chunks content, and stores embeddings in the
vector database.

## Development

To run the service locally:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

## Health Check

The service provides a health check endpoint at `/health`.
