# GenAI API Microservice

This is the GenAI API microservice for the RAG-powered chatbot system.

## Development

To run the service locally:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

## Health Check

The service provides a health check endpoint at `/health`.
