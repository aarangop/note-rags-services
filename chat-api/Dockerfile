FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy the db package first (this is the dependency)
COPY db/ ../db/

# Copy project files
COPY chat-api/pyproject.toml ./
COPY chat-api/uv.lock ./

# Install dependencies
RUN uv sync

# Copy source code
COPY chat-api/app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
