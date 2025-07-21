# RAG-Powered Chatbot API

A microservice-based RAG (Retrieval Augmented Generation) chatbot system built
with FastAPI and orchestrated using Podman Compose.

## Architecture

The system consists of the following microservices:

- **genai-api** (Port 8000): Handles GenAI interactions and conversations
- **ingestion-api** (Port 8001): Processes file changes, chunks content, and
  manages embeddings
- **postgres**: Database with PgVector extension for vector storage
- **redis**: Caching layer for improved performance

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Podman and podman-compose

## Quick Start

1. Install dependencies for each service:

   ```bash
   cd genai-api && uv sync && cd ..
   cd ingestion-api && uv sync && cd ..
   ```

2. Start all services:

   ```bash
   podman-compose up -d
   ```

3. Check service health:
   - Chat API: http://localhost:8000/health
   - Ingestion API: http://localhost:8001/health

## Development

### Running Individual Services

**Chat API:**

```bash
cd genai-api
uv run uvicorn app.main:app --reload --port 8000
```

**Ingestion API:**

```bash
cd ingestion-api
uv run uvicorn app.main:app --reload --port 8001
```

### Database Access

The PostgreSQL database is available at `localhost:5432` with:

- Database: `notes_rag`
- Username: `postgres`
- Password: `postgres`

### Redis Access

Redis is available at `localhost:6379`.

## API Documentation

Once running, API documentation is available at:

- Chat API: http://localhost:8000/docs
- Ingestion API: http://localhost:8001/docs

## Project Structure

```
note-rags-api/
├── genai-api/          # GenAI microservice
├── ingestion-api/      # Data ingestion microservice
├── scripts/            # Database initialization scripts
├── podman-compose.yml  # Service orchestration
└── README.md
```

## Next Steps

The APIs are scaffolded with basic health check endpoints. You can now
implement:

1. **Chat API**: Chat sessions, message handling, RAG pipeline integration
2. **Ingestion API**: File processing, chunking algorithms, embedding generation
3. **Database Models**: SQLAlchemy models for your data structures
4. **Authentication**: User authentication and authorization
5. **Monitoring**: Logging, metrics, and observability
