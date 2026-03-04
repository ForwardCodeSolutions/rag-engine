# Audit Technical Spec

Implementation details for each fix from `audit-fixes.md`.

---

## КРИТИЧНО

### AUTH-1: API Authentication middleware

**Файлы:**
- Создать `src/rag_engine/api/dependencies.py`
- Изменить `src/rag_engine/api/routes/gdpr.py`
- Изменить `src/rag_engine/api/routes/health.py` (без auth)
- Изменить `src/rag_engine/api/app.py`

**Реализация:**
- Создать `verify_api_key(x_api_key: str = Header(...))` — dependency, сравнивает с `Settings().api_key`
- Возвращает `HTTPException(401)` при неверном ключе
- `/health` — без auth (публичный)
- Все остальные endpoints — `Depends(verify_api_key)`

**Тесты:**
- Запрос без заголовка → 401
- Запрос с неверным ключом → 401
- Запрос с верным ключом → 200
- `/health` без ключа → 200

---

### AUTH-2: Обязательный api_key

**Файлы:**
- `src/rag_engine/models/config.py`

**Реализация:**
- Убрать default `"changeme"` — оставить `api_key: str` без значения по умолчанию
- pydantic-settings выбросит `ValidationError` при старте, если `API_KEY` не задан в `.env`
- Обновить `.env.example` — добавить комментарий `# REQUIRED`

**Тесты:**
- Проверить что `Settings(api_key="test-key")` работает
- Проверить что `Settings()` без env → `ValidationError` (мокнуть environment)

---

### GDPR-1: QdrantStore в GDPR routes

**Файлы:**
- `src/rag_engine/api/routes/gdpr.py`

**Реализация:**
- Добавить `_qdrant_store = QdrantStore(client=QdrantClient(...))` к module-level singletons
- Передать в `GDPRService(_bm25_store, _graph_store, _qdrant_store)`
- Или (лучше, совместить с CODE-3): перейти на DI через `Depends()`

**Тесты:**
- Integration тест: добавить вектор в Qdrant → DELETE document → verify вектор удалён
- Существующие unit-тесты GDPR уже проверяют каскад с `qdrant_store`

---

### GDPR-2: Реальный documents_removed

**Файлы:**
- `src/rag_engine/services/gdpr.py` — `delete_tenant_data()` должен возвращать `dict`
- `src/rag_engine/api/routes/gdpr.py` — использовать возвращённый count
- `src/rag_engine/models/gdpr.py` — обновить `GDPRDeleteResponse` (добавить breakdown)

**Реализация:**
- `GDPRService.delete_tenant_data()` → считать количество удалённых документов из каждого backend перед `clear_tenant()`
- Или: каждый store `.clear_tenant()` возвращает count вместо `None`
- Route подставляет реальные значения в response

**Тесты:**
- Добавить документы → delete_tenant → assert `documents_removed > 0`

---

### DOCKER-1: Dockerfile

**Файлы:**
- Создать `Dockerfile`

**Реализация:**
```dockerfile
# Stage 1: build
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
```

**Тесты:**
- `docker build .` succeeds (manual/CI)

---

### DOCKER-2: .dockerignore

**Файлы:**
- Создать `.dockerignore`

**Содержимое:**
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
*.md
!README.md
```

---

### STORE-1: Детерминистичный point ID

**Файлы:**
- `src/rag_engine/storage/qdrant_store.py`

**Реализация:**
```python
import hashlib

def _point_id(document_id: str, chunk_index: int) -> int:
    key = f"{document_id}:{chunk_index}"
    digest = hashlib.sha256(key.encode()).hexdigest()
    return int(digest[:16], 16)  # 64-bit integer from first 16 hex chars
```
- Заменить `abs(hash(...)) % (2**63)` на вызов `_point_id()`

**Тесты:**
- Один и тот же input → одинаковый ID в разных вызовах
- Разные inputs → разные IDs
- Upsert того же документа дважды → count не увеличивается (идемпотентность)

---

### API-1: POST /api/v1/documents/upload

**Файлы:**
- Создать `src/rag_engine/api/routes/documents.py`
- Обновить `src/rag_engine/api/routes/__init__.py`
- Обновить `src/rag_engine/api/app.py`

**Реализация:**
- Принимает `UploadFile` + `tenant_id` (Form) + `document_type` (Form, default "general") + `language` (Form, optional)
- Сохраняет во временный файл → `ingest_document()` → чанки в BM25 + KG
- Embedding + Qdrant (если EmbeddingService доступен)
- Возвращает `DocumentResponse` с `document_id`, `chunk_count`, `language`

**Тесты:**
- Upload .txt файл → 200, chunk_count > 0
- Upload неподдерживаемый формат → 400/422
- Upload пустой файл → 400
- Upload с auth header → 200; без → 401

---

### API-2: POST /api/v1/documents/search

**Файлы:**
- Добавить в `src/rag_engine/api/routes/documents.py`

**Реализация:**
- Принимает `SearchQuery` (JSON body)
- Вызывает `HybridRetriever.search()` с параметрами из запроса
- Для vector: если EmbeddingService доступен → encode query → Qdrant search → pass as vector_results
- Возвращает `SearchResponse`

**Тесты:**
- Search с данными → results > 0
- Search пустой индекс → results = []
- Search с разными `search_type` → корректная фильтрация
- Search без auth → 401

---

### TEST-1: Обновление тестов

**Файлы:**
- Все тестовые файлы с API-вызовами
- Создать `tests/unit/test_auth.py`
- Создать `tests/unit/test_documents_endpoint.py`

**Реализация:**
- Добавить `X-API-Key` header во все TestClient вызовы (или fixture)
- Новые тесты для auth (401/200)
- Новые тесты для upload и search endpoints
- Добавить fixture-файлы для PDF/DOCX парсеров в `tests/fixtures/`

---

### DOCS-1: Обновить README.md

**Файлы:**
- `README.md`
- `docs/api.md`

**Реализация:**
- Добавить примеры curl с `-H "X-API-Key: ..."` header
- Добавить upload и search endpoint примеры
- Обновить список endpoints в разделе API
- Добавить раздел Authentication

---

## РЕКОМЕНДОВАНО

### SEC-1: CORS middleware

**Файлы:** `src/rag_engine/api/app.py`, `src/rag_engine/models/config.py`

- Добавить `cors_origins: str = "http://localhost:3000"` в Settings
- `app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), ...)`
- `CORS_ORIGINS` в `.env.example`

---

### SEC-2: Rate limiting

**Файлы:** `src/rag_engine/api/app.py`, `pyproject.toml`

- Добавить `slowapi` в зависимости
- Limiter на DELETE endpoints: `"10/minute"`
- Limiter на search: `"60/minute"`

---

### SEC-3: Валидация ID

**Файлы:** `src/rag_engine/api/dependencies.py`

- `VALID_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')`
- Dependency `validate_tenant_id()` и `validate_document_id()`
- `query: str = Field(max_length=2000)` в SearchQuery

---

### TEST-2: Тесты парсеров

**Файлы:** `tests/fixtures/sample.pdf`, `tests/fixtures/sample.docx`, `tests/unit/test_ingestion.py`

- Создать минимальные fixture-файлы (1 страница)
- Тесты: parse → text не пустой, содержит ожидаемый контент
- Тесты error paths: повреждённый файл → IngestionError

---

### DOCKER-3: Healthcheck для qdrant

**Файлы:** `docker-compose.yml`

```yaml
qdrant:
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:6333/healthz || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 3
  ...
api:
  depends_on:
    qdrant:
      condition: service_healthy
```

---

### DOCKER-4: Пиннинг версии qdrant

**Файлы:** `docker-compose.yml`

- `image: qdrant/qdrant:v1.13.2` (или актуальная стабильная)

---

### DOCS-2: Обновить models.md

**Файлы:** `docs/models.md`

- Убрать `TenantConfig` (не существует в коде)
- Добавить `DocumentDeleteResponse`, `GDPRDeleteResponse`
- Привести в соответствие с реальными Pydantic-моделями

---

### CODE-1: Return type на EmbeddingService.model

**Файлы:** `src/rag_engine/services/embedding.py`

- `from __future__ import annotations` + `-> "SentenceTransformer"` или `-> Any`

---

### CODE-2: BaseStore ABC

**Файлы:** создать `src/rag_engine/storage/base.py`

```python
class BaseStore(ABC):
    @abstractmethod
    def add_documents(self, tenant_id: str, ...) -> int: ...
    @abstractmethod
    def remove_document(self, tenant_id: str, document_id: str) -> int: ...
    @abstractmethod
    def clear_tenant(self, tenant_id: str) -> None: ...
    @abstractmethod
    def clear(self) -> None: ...
```

- BM25Store, KnowledgeGraphStore, QdrantStore наследуют от BaseStore

---

### CODE-3: Dependency injection

**Файлы:** `src/rag_engine/api/dependencies.py`, `src/rag_engine/api/routes/gdpr.py`

- `get_gdpr_service() -> GDPRService` — factory function
- Routes получают service через `Depends(get_gdpr_service)`
- Убрать module-level `_bm25_store`, `_graph_store`, `_gdpr_service`
