FROM python:3.11-slim

WORKDIR /workspace

# Install uv
RUN pip install uv

# Set UV to use a different venv location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy the workspace pyproject.toml and uv.lock first
COPY pyproject.toml uv.lock ./

# Copy the db package (workspace dependency)
COPY db/ ./db/

# Copy chat-api project files
COPY chat-api/ ./chat-api/

# Install dependencies
RUN uv sync

# Set working directory to chat-api
WORKDIR /workspace/chat-api

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
