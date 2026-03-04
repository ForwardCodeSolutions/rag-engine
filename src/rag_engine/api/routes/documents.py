"""Document upload and search API endpoints."""

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from rag_engine.api.dependencies import verify_api_key
from rag_engine.core.hybrid_retriever import HybridRetriever
from rag_engine.ingestion.pipeline import ingest_document
from rag_engine.models.document import DocumentResponse, DocumentType
from rag_engine.models.search import SearchQuery, SearchResponse
from rag_engine.storage.bm25_store import BM25Store
from rag_engine.storage.knowledge_graph import KnowledgeGraphStore

router = APIRouter(tags=["documents"], dependencies=[Depends(verify_api_key)])

# Shared store instances (will be replaced with dependency injection later)
_bm25_store = BM25Store()
_graph_store = KnowledgeGraphStore()
_retriever = HybridRetriever(_bm25_store, _graph_store)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    tenant_id: str = Form(description="Tenant identifier"),
    document_type: str = Form(default="general", description="general|legal|technical"),
    language: str | None = Form(default=None, description="Language hint (auto-detected)"),
) -> DocumentResponse:
    """Upload a document for parsing, chunking, and indexing.

    Supports PDF, DOCX, TXT, and MD files. Chunks are indexed
    into BM25 and Knowledge Graph for hybrid retrieval.
    """
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    # Validate document_type
    try:
        doc_type = DocumentType(document_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_type '{document_type}'. Use: general, legal, technical",
        ) from exc

    # Save upload to temp file
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty file")
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        chunks, detected_language = ingest_document(
            file_path=tmp_path,
            document_type=doc_type,
            language_hint=language,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    document_id = str(uuid.uuid4())

    # Index chunks into BM25
    index_chunks = [(document_id, chunk.index, chunk.text) for chunk in chunks]
    _bm25_store.add_documents(tenant_id, detected_language, index_chunks)

    # Index chunks into Knowledge Graph
    _graph_store.add_documents(tenant_id, index_chunks)

    return DocumentResponse(
        id=document_id,
        filename=filename,
        tenant_id=tenant_id,
        language=detected_language,
        chunk_count=len(chunks),
    )


@router.post("/documents/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery) -> SearchResponse:
    """Search across indexed documents using hybrid retrieval.

    Combines BM25 keyword search and Knowledge Graph traversal.
    Vector search results can be passed when Qdrant is configured.
    """
    results = _retriever.search(
        tenant_id=query.tenant_id,
        query=query.query,
        language=query.language or "en",
        top_k=query.top_k,
        search_type=query.search_type,
    )

    return SearchResponse(
        query=query.query,
        results=results,
        total_results=len(results),
    )
