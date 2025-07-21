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

# Copy genai-api project files
COPY genai-api/ ./genai-api/

# Install dependencies
RUN uv sync

# Set working directory to genai-api
WORKDIR /workspace/genai-api

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
