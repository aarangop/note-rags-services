# Stage 1: Base stage with uv and dependencies
FROM python:3.10-slim AS dependencies

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /workspace

# Install uv
RUN pip install uv

# Set UV to use a different venv location that appuser can access
ENV UV_PROJECT_ENVIRONMENT=/home/appuser/.venv

# Create all necessary directories with proper permissions
RUN mkdir -p /home/appuser/.cache \
    && mkdir -p /home/appuser/.local/share/uv \
    && mkdir -p /home/appuser/.local/state/uv \
    && mkdir -p /home/appuser/.venv \
    && chown -R appuser:appuser /home/appuser \
    && chown -R appuser:appuser /workspace

# Copy dependency files first (for better caching)
COPY pyproject.toml uv.lock ./

# Copy the db package (workspace dependency) - only structure needed for deps
COPY db/pyproject.toml ./db/
COPY db/src/ ./db/src/

# Copy ingestion-api dependency files
COPY ingestion-api/pyproject.toml ./ingestion-api/

# Install dependencies (this layer will be cached unless dependencies change)
RUN uv sync \
    && chown -R appuser:appuser /home/appuser/.venv

# Stage 2: Runtime stage with application code
FROM python:3.10-slim AS runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /workspace

# Copy the virtual environment from the dependencies stage
COPY --from=dependencies --chown=appuser:appuser /home/appuser/.venv /home/appuser/.venv

# Add the venv to PATH so we can run python directly
ENV PATH="/home/appuser/.venv/bin:$PATH"

# Copy workspace configuration
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Copy the db package (complete)
COPY --chown=appuser:appuser db/ ./db/

# Copy ingestion-api project files (this will change frequently)
COPY --chown=appuser:appuser ingestion-api/ ./ingestion-api/

# Ensure proper ownership
RUN chown -R appuser:appuser /workspace

# Switch to non-root user
USER appuser

# Set working directory to ingestion-api
WORKDIR /workspace/ingestion-api

# Expose port
EXPOSE 8001

# Run the application using the virtual environment directly
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
