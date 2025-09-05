# Stage 1: Base dependencies
FROM python:3.11-slim AS base

WORKDIR /workspace

# Install uv
RUN pip install uv

FROM base AS base_deps

# Set UV to use a different venv location
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
 
# Copy the workspace pyproject.toml and uv.lock first
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync

# Stage 2: Project dependencies (other project libraries)
FROM base_deps AS project_deps

# Copy the db package (workspace dependency)
COPY db/ ./db/

# Copy the auth-lib package (workspace dependency)
COPY auth-lib/ ./auth-lib/

# Stage 3: Production stage
FROM project_deps AS prod

# Copy notes-api project files
COPY notes-api/ ./notes-api/

# Set working directory to notes-api
WORKDIR /workspace/notes-api

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "fastapi", "run", "app/main.py", "--port", "8000"]
