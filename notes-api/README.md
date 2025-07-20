# Notes API

A FastAPI microservice for managing notes within the note-rags system.

## Overview

The Notes API provides endpoints for creating, reading, updating, and deleting
notes. It's part of the larger note-rags system for RAG-powered applications.

## Features

- Health check endpoint for monitoring
- Database connectivity checks
- FastAPI-based REST API
- Async/await support
- CORS middleware for cross-origin requests

## API Endpoints

### Health Check

- `GET /health` - Basic health check
- `GET /health/` - Detailed health check with database status

### Root

- `GET /` - API information

## Development

### Prerequisites

- Python 3.11+
- uv package manager

### Installation

```bash
uv sync
```

### Running the API

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Testing

The API will be available at:

- Health endpoint: http://localhost:8002/health
- API docs: http://localhost:8002/docs
- OpenAPI spec: http://localhost:8002/openapi.json

## Docker

Build and run with Docker:

```bash
docker build -t notes-api .
docker run -p 8002:8002 notes-api
```

## Configuration

The API uses environment variables for configuration:

- `DB_URL` - Database URL
- `DB_USERNAME` - Database username
- `DB_PASSWORD` - Database password

Configuration is loaded from a `.env` file in the parent directory.
