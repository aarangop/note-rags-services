#!/bin/bash

# Development setup script

echo "🚀 Setting up RAG-Powered Chatbot API development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo "❌ podman-compose is not installed. Please install it first."
    exit 1
fi

echo "📦 Installing dependencies for chat-api..."
cd chat-api && uv sync
if [ $? -ne 0 ]; then
    echo "❌ Failed to install chat-api dependencies"
    exit 1
fi
cd ..

echo "📦 Installing dependencies for ingestion-api..."
cd ingestion-api && uv sync
if [ $? -ne 0 ]; then
    echo "❌ Failed to install ingestion-api dependencies"
    exit 1
fi
cd ..

echo "🐳 Starting services with podman-compose..."
podman-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🔍 Checking service health..."

# Check chat-api health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Chat API is healthy"
else
    echo "❌ Chat API is not responding"
fi

# Check ingestion-api health
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Ingestion API is healthy"
else
    echo "❌ Ingestion API is not responding"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Service URLs:"
echo "   Chat API:      http://localhost:8000"
echo "   Ingestion API: http://localhost:8001"
echo "   API Docs:      http://localhost:8000/docs"
echo "                  http://localhost:8001/docs"
echo ""
echo "🗄️ Database:"
echo "   PostgreSQL:    localhost:5432"
echo "   Redis:         localhost:6379"
echo ""
echo "🛠️ Useful commands:"
echo "   View logs:     podman-compose logs -f"
echo "   Stop services: podman-compose down"
echo "   Restart:       podman-compose restart"
