---
name: docker-build
description: Rules for Dockerfile and docker-compose in rag-engine. Use when creating or modifying Docker configuration.
---
## Dockerfile Rules
- Multi-stage build: builder (install deps) → runtime (copy only .venv and src)
- Base image: `python:3.11-slim` (matches requires-python in pyproject.toml)
- Use uv for package installation (copy from `ghcr.io/astral-sh/uv:latest`)
- Non-root user: `useradd --create-home appuser`, switch with `USER appuser`
- Expose port 8000
- CMD: `.venv/bin/uvicorn rag_engine.api.app:app --host 0.0.0.0 --port 8000`
- No secrets in Dockerfile (use env_file in compose)

## .dockerignore Must Include
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
tests/
docs/
.git/
.github/
.env
.env.*
```

## docker-compose.yml Rules
- Container names: `rag_` prefix (rag_api, rag_qdrant)
- Ports: API=8000, Qdrant=6333 (per playbook port table)
- Pin qdrant image version (not :latest)
- Healthcheck on qdrant:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:6333/healthz || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 3
  ```
- api depends_on qdrant with `condition: service_healthy`
- env_file: .env (never hardcode secrets in compose)
- volumes for qdrant persistent storage

## Verification
After any Docker change:
1. `docker compose config` — validate compose syntax
2. `docker build .` — verify Dockerfile builds
3. `docker compose up -d` — verify services start
4. `curl http://localhost:8000/api/v1/health` — verify API responds
