# Stage 1: install dependencies
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --frozen
COPY src/ src/

# Stage 2: runtime
FROM python:3.11-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY --from=builder /app/src src
USER appuser
EXPOSE 8000
CMD [".venv/bin/uvicorn", "rag_engine.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
