# Use uv base image with Python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy lockfiles first to maximize layer cache
COPY pyproject.toml uv.lock ./

# Copy lockfiles + README before uv sync
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Copy application code and runtime data
COPY src ./src
COPY data ./data

# Runtime config
ENV PYTHONPATH=/app/src \
    FIT_DB_PATH=/app/data/nutrition.db \
    PORT=5002

EXPOSE 5002

# Render sets $PORT; default to 5002 locally
CMD ["sh", "-c", "uv run -m uvicorn fit.backend.main:app --host 0.0.0.0 --port ${PORT}"]
