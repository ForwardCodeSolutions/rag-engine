"""Search-related Pydantic models."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SearchType(StrEnum):
    """Available retrieval methods."""

    HYBRID = "hybrid"
    VECTOR = "vector"
    BM25 = "bm25"
    GRAPH = "graph"


class SearchQuery(BaseModel):
    """Request model for document search."""

    query: str = Field(max_length=2000, description="Search text")
    tenant_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$", description="Tenant identifier")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    search_type: SearchType = Field(
        default=SearchType.HYBRID, description="Retrieval method to use"
    )
    language: str | None = Field(default=None, description="Language filter")


class SearchResult(BaseModel):
    """Single search result item."""

    document_id: str = Field(description="Source document identifier")
    chunk_text: str = Field(description="Matched text chunk")
    score: float = Field(description="Combined relevance score")
    retrieval_method: str = Field(description="Which method found this result")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional chunk metadata")


class SearchResponse(BaseModel):
    """Response model wrapping multiple search results."""

    query: str = Field(description="Original search query")
    results: list[SearchResult] = Field(default_factory=list, description="Ranked results")
    total_results: int = Field(description="Total number of results found")
