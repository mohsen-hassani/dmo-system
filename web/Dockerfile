# syntax=docker/dockerfile:1

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

# Copy workspace configuration
COPY pyproject.toml uv.lock ./
COPY web ./web

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package dmo-web

# =============================================================================
# Runtime Stage: Minimal production image
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/web/src ./web/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "web/src/dmo_web/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
