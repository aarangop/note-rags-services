FROM python:3.10-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /workspace

# Install uv
RUN pip install uv

# Set UV to use a different venv location that appuser can access
ENV UV_PROJECT_ENVIRONMENT=/home/appuser/.venv

# Copy the workspace pyproject.toml and uv.lock first
COPY pyproject.toml uv.lock ./

# Copy the db package (workspace dependency)
COPY db/ ./db/

# Copy ingestion-api project files
COPY ingestion-api/ ./ingestion-api/

# Create all necessary directories with proper permissions before switching to appuser
RUN mkdir -p /home/appuser/.cache \
    && mkdir -p /home/appuser/.local/share/uv \
    && mkdir -p /home/appuser/.local/state/uv \
    && mkdir -p /home/appuser/.venv \
    && chown -R appuser:appuser /home/appuser \
    && chown -R appuser:appuser /workspace

# Install dependencies (still as root)
RUN uv sync \
    && chown -R appuser:appuser /home/appuser/.venv

# Switch to non-root user
USER appuser

# Set working directory to ingestion-api
WORKDIR /workspace/ingestion-api

# Expose port
EXPOSE 8001

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
