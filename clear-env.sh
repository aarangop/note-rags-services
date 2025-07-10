#!/bin/bash

# Clear any existing environment variables that might be cached
unset OPENAI_API_KEY
unset DB_URL
unset DB_USERNAME
unset DB_PASSWORD
unset DATABASE_URL
unset DATABASE_USER
unset DATABASE_PASSWORD

echo "Environment variables cleared. Now you can restart your services."
echo ""
echo "To run services:"
echo "  Chat API:      cd chat-api && uv run uvicorn app.main:app --reload --port 8000"
echo "  Ingestion API: cd ingestion-api && uv run uvicorn app.main:app --reload --port 8001"
echo ""
echo "Services will now load from the shared .env.shared file."
