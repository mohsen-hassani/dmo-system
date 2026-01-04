# =============================================================================
# Builder Stage: Install dependencies with UV
# =============================================================================
FROM python:3.11-slim AS builder

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set UV environment variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Copy workspace configuration (UV needs all pyproject.toml files)
COPY pyproject.toml uv.lock ./
COPY core ./core
COPY api ./api

# Install dependencies with cache mount
# Note: --extra postgres installs asyncpg for PostgreSQL support
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package dmo-api --extra postgres

# =============================================================================
# Runtime Stage: Minimal production image
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code (not tests)
COPY --from=builder /app/core/src ./core/src
COPY --from=builder /app/api/src ./api/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run uvicorn server
CMD ["uvicorn", "dmo_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
