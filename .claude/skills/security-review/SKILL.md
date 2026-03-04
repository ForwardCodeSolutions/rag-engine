---
name: security-review
description: Security checklist for rag-engine. Run before any release or after adding new endpoints/features.
---
## Authentication
- [ ] All endpoints (except /health) require X-API-Key header
- [ ] API key loaded from Settings (env var), no hardcoded defaults
- [ ] Invalid/missing key returns 401 with generic message (no key leak)
- [ ] /health is public (no auth required)

## CORS
- [ ] CORSMiddleware configured in app.py
- [ ] allow_origins is explicit whitelist (NOT `["*"]`)
- [ ] CORS_ORIGINS configurable via .env

## Rate Limiting
- [ ] DELETE endpoints: max 10/minute per IP
- [ ] Search endpoint: max 60/minute per IP
- [ ] Rate limit responses return 429 with Retry-After header

## Input Validation
- [ ] tenant_id: `^[a-zA-Z0-9_-]{1,128}$` — no special chars, max length
- [ ] document_id: same pattern as tenant_id
- [ ] query: max_length=2000 in SearchQuery model
- [ ] language: validated against known codes (en, it, ru)
- [ ] File uploads: validate extension before parsing

## File Handling
- [ ] Uploaded files saved to temp dir, not user-controlled path
- [ ] file_path.resolve() checked against allowed base directory
- [ ] Temp files cleaned up after processing

## Storage Security
- [ ] Qdrant point IDs use hashlib.sha256 (deterministic, no hash())
- [ ] Qdrant port not exposed to public network in production
- [ ] No raw user input in collection names (sanitized tenant_id)

## GDPR
- [ ] Delete cascades to ALL backends (BM25 + KG + Qdrant)
- [ ] Audit log on every delete operation
- [ ] No orphaned data after deletion

## Secrets
- [ ] .env in .gitignore
- [ ] .env.*, *.pem, *.key, credentials.json in .gitignore
- [ ] No secrets in Dockerfile, docker-compose.yml, or source code
- [ ] API_KEY is required (no default value)
