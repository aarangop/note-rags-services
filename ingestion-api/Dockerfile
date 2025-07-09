FROM python:3.13-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files with specific ownership
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser uv.lock ./

# Install dependencies
RUN uv sync

# Copy only necessary source code (exclude sensitive files)
COPY --chown=appuser:appuser app/ ./app/
# Add other specific directories as needed
# COPY --chown=appuser:appuser static/ ./static/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
