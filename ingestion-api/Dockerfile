FROM python:3.10-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files with specific ownership
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser uv.lock ./

# Copy environment file for development
COPY --chown=appuser:appuser .env ./

# Create all necessary directories with proper permissions before switching to appuser
RUN mkdir -p /home/appuser/.cache \
    && mkdir -p /home/appuser/.local/share/uv \
    && mkdir -p /home/appuser/.local/state/uv \
    && chown -R appuser:appuser /home/appuser

# Install dependencies (still as root)
RUN uv sync

# Copy only necessary source code (exclude sensitive files)
COPY --chown=appuser:appuser app/ ./app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
