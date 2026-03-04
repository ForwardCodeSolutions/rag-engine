# Audit Fix Plan

Post-audit checklist. Mark `[x]` when done, add commit hash.

## КРИТИЧНО (блокирует публикацию)

- [x] **AUTH-1** API Authentication — middleware X-API-Key, `Depends()`, `/health` без auth
- [x] **AUTH-2** Убрать hardcoded `"changeme"` — `api_key` обязательный, приложение не стартует без него
- [x] **GDPR-1** Каскадное удаление — подключить QdrantStore к GDPRService в routes
- [x] **GDPR-2** `documents_removed` — возвращать реальное количество, не 0
- [x] **DOCKER-1** Dockerfile — multi-stage, python:3.11-slim, uv, non-root user
- [x] **DOCKER-2** .dockerignore
- [x] **STORE-1** `hash()` → `hashlib.sha256` для Qdrant point IDs (детерминистичный)
- [x] **API-1** `POST /api/v1/documents/upload` endpoint
- [x] **API-2** `POST /api/v1/documents/search` endpoint
- [x] **TEST-1** Обновить тесты — auth header, новые endpoints, парсеры
- [x] **DOCS-1** Обновить README.md — upload, search, auth в примерах curl

## РЕКОМЕНДОВАНО (после критического)

- [x] **SEC-1** CORS middleware с whitelist origins
- [x] **SEC-2** Rate limiting (slowapi) на деструктивные endpoints
- [x] **SEC-3** Валидация `tenant_id`/`document_id` — длина, формат, запрещённые символы
- [x] **TEST-2** Тесты парсеров PDF/DOCX с fixture-файлами (покрытие с 38%/50% до >80%)
- [x] **DOCKER-3** Healthcheck в docker-compose для qdrant
- [x] **DOCKER-4** Пиннинг версии qdrant в docker-compose
- [x] **DOCS-2** `docs/models.md` — привести в соответствие с реальным кодом
- [x] **CODE-1** Return type на `EmbeddingService.model` property
- [x] **CODE-2** `BaseStore` ABC для `storage/*`
- [x] **CODE-3** Dependency injection вместо module-level singletons в gdpr routes
