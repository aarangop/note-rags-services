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

# Copy the auth-lib package (workspace dependency)
COPY auth-lib/ ./auth-lib/

# Copy notes-api project files
COPY notes-api/ ./notes-api/

# Install dependencies
RUN uv sync

# Set working directory to notes-api
WORKDIR /workspace/notes-api

# Expose port
EXPOSE 8002

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
