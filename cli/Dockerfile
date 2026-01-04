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

# Copy workspace configuration (UV needs core package too)
COPY pyproject.toml uv.lock ./
COPY core ./core
COPY cli ./cli

# Install dependencies with cache mount
# Include postgres extra for database access
RUN --mount=type=cache,target=/root/.cache/uv \
    cd core && uv pip install -e ".[postgres]" && cd .. && \
    uv sync --frozen --no-dev --package dmo-cli

# =============================================================================
# Runtime Stage: Minimal production image
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code
COPY --from=builder /app/core/src ./core/src
COPY --from=builder /app/cli/src ./cli/src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default command shows help
CMD ["dmo", "--help"]
