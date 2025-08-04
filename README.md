# Note RAGs Services

A comprehensive microservice-based RAG (Retrieval Augmented Generation) system
for note-taking and knowledge management. The system processes documents,
generates embeddings, and provides AI-powered chat capabilities over your
personal knowledge base.

## What is Note RAGs?

Note RAGs is a complete solution for building a personal knowledge management
system with AI capabilities. It ingests your documents (PDFs, Markdown files),
chunks and embeds them using OpenAI, stores them in a vector database, and
provides a conversational AI interface to query your knowledge base.

## System Architecture

The system consists of 6 main components organized as a monorepo workspace:

### Core APIs

- **🔐 auth-api** (Port 8004): JWT-based authentication service with user
  management
- **📝 notes-api** (Port 8003): Notes and document management with
- **🧠 genai-api** (Port 8002): RAG pipeline with OpenAI integration for chat
  and queries
- **📥 ingestion-api** (Port 8001): File processing, chunking, and embedding
  generation

### Shared Libraries

- **🔑 auth-lib**: Shared JWT authentication utilities with RSA key management
- **🗄️ db**: Database schemas, migrations, and CLI tools with pgvector support

### Infrastructure

- **PostgreSQL**: Primary database with pgvector extension for vector similarity
  search
- **Redis**: Caching layer for improved performance

## Key Features

- **Document Processing**: Automatic ingestion of PDF and Markdown files
- **Vector Search**: Semantic search using OpenAI embeddings and pgvector
- **AI Chat**: Conversational interface with context-aware responses
- **Authentication**: Complete JWT-based auth system with refresh tokens
- **GraphQL**: Modern API interface for notes management
- **Streaming**: Real-time streaming responses for chat interactions
- **Microservices**: Scalable architecture with clear service boundaries

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Podman and podman-compose
- OpenAI API key

## Quick Start

1. **Clone and install dependencies:**

   ```bash
   git clone <repository>
   cd services
   uv sync
   ```

2. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and database credentials
   ```

3. **Start all services:**

   ```bash
   podman-compose up -d
   ```

4. **Initialize the database:**

   ```bash
   uv run note-rags-db init --database-url localhost:5432/notes_rag
   uv run note-rags-db upgrade --database-url localhost:5432/notes_rag
   ```

5. **Check service health:**
   - Auth API: http://localhost:8004/health
   - Notes API: http://localhost:8003/health
   - GenAI API: http://localhost:8002/health
   - Ingestion API: http://localhost:8001/health

## Development

### Running Individual Services

```bash
# Auth API
cd auth-api && uv run uvicorn app.main:app --reload --port 8004

# Notes API
cd notes-api && uv run uvicorn app.main:app --reload --port 8003

# GenAI API
cd genai-api && uv run uvicorn app.main:app --reload --port 8002

# Ingestion API
cd ingestion-api && uv run uvicorn app.main:app --reload --port 8001
```

### Testing

```bash
# Run all tests
uv run pytest

# Run tests for specific service
cd auth-api && uv run pytest
cd genai-api && uv run pytest -m unit
```

### Database Management

The `note-rags-db` CLI provides database management:

```bash
# Initialize database with extensions
uv run note-rags-db init --database-url localhost:5432/notes_rag

# Run migrations
uv run note-rags-db upgrade --database-url localhost:5432/notes_rag
```

## API Documentation

Interactive API documentation is available when services are running:

- **Auth API**: http://localhost:8004/docs
- **Notes API**: http://localhost:8003/docs (REST) + GraphQL playground
- **GenAI API**: http://localhost:8002/docs
- **Ingestion API**: http://localhost:8001/docs

## Project Structure

```
services/
├── auth-api/           # Authentication microservice
├── auth-lib/           # Shared JWT authentication library
├── notes-api/          # Notes management with GraphQL
├── genai-api/          # RAG pipeline and chat interface
├── ingestion-api/      # Document processing and embedding
├── db/                 # Database schemas and migrations
├── podman-compose.yml  # Container orchestration
└── pyproject.toml      # Workspace configuration
```

## Usage Example

1. **Register a user:**

   ```bash
   curl -X POST http://localhost:8004/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"SecurePass123"}'
   ```

2. **Upload a document:**

   ```bash
   curl -X POST http://localhost:8001/file_events/ \
     -H "Content-Type: application/json" \
     -d '{"file_path":"/path/to/document.pdf","change_type":"created"}'
   ```

3. **Query your knowledge base:**
   ```bash
   curl -X POST http://localhost:8002/queries/ \
     -H "Content-Type: application/json" \
     -d '{"text":"What are the key concepts in my documents?"}'
   ```

## Configuration

Key environment variables:

- `OPENAI_API_KEY`: Required for embeddings and chat
- `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`: Database connection
- `REDIS_URL`: Redis connection for caching
- `JWT_PRIVATE_KEY_PATH`, `JWT_PUBLIC_KEY_PATH`: RSA keys for JWT signing

## License

MIT License - see LICENSE file for details.
