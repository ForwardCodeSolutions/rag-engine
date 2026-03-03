"""Knowledge graph store using NetworkX for entity-relationship retrieval."""

import re
from dataclasses import dataclass, field

import networkx as nx
import structlog

logger = structlog.get_logger()

# Patterns for extracting entities from text (capitalized multi-word phrases)
ENTITY_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")

# Common words that start sentences but are not entities
STOP_WORDS = frozenset(
    {
        "The",
        "This",
        "That",
        "These",
        "Those",
        "There",
        "What",
        "When",
        "Where",
        "Which",
        "While",
        "Who",
        "How",
        "However",
        "Here",
        "His",
        "Her",
        "Its",
        "Our",
        "Your",
        "Their",
        "Some",
        "Any",
        "All",
        "But",
        "And",
        "For",
        "Not",
        "From",
        "Into",
        "With",
        "After",
        "Before",
        "During",
        "Between",
        "Each",
        "Every",
        "Other",
        "Another",
        "Such",
    }
)


@dataclass
class GraphChunk:
    """A chunk linked to entities in the knowledge graph."""

    document_id: str
    chunk_index: int
    text: str
    entities: list[str] = field(default_factory=list)


def extract_entities(text: str) -> list[str]:
    """Extract named entities from text using capitalization heuristics.

    Finds capitalized multi-word phrases (e.g. "European Union",
    "Machine Learning") that likely represent named entities.

    Args:
        text: Text to extract entities from.

    Returns:
        Deduplicated list of entity strings.
    """
    matches = ENTITY_PATTERN.findall(text)
    entities: list[str] = []
    for match in matches:
        # Strip leading stop words from multi-word matches
        words = match.split()
        while words and words[0] in STOP_WORDS:
            words.pop(0)
        cleaned = " ".join(words)
        if len(cleaned) > 2:
            entities.append(cleaned)
    return list(dict.fromkeys(entities))


class KnowledgeGraphStore:
    """In-memory knowledge graph with per-tenant isolation.

    Builds a NetworkX graph where:
    - Entity nodes represent named entities extracted from chunks
    - Chunk nodes represent text chunks containing those entities
    - Edges connect chunks to the entities they mention
    - Co-occurrence edges connect entities found in the same chunk

    Search traverses the graph from query-matching entities to find
    related chunks.
    """

    def __init__(self) -> None:
        self._graphs: dict[str, nx.Graph] = {}
        self._chunks: dict[str, dict[str, GraphChunk]] = {}

    def _get_graph(self, tenant_id: str) -> nx.Graph:
        """Get or create a graph for a tenant."""
        if tenant_id not in self._graphs:
            self._graphs[tenant_id] = nx.Graph()
            self._chunks[tenant_id] = {}
        return self._graphs[tenant_id]

    def _chunk_node_id(self, document_id: str, chunk_index: int) -> str:
        """Create a unique node ID for a chunk."""
        return f"chunk:{document_id}:{chunk_index}"

    def _entity_node_id(self, entity: str) -> str:
        """Create a unique node ID for an entity."""
        return f"entity:{entity.lower()}"

    def add_documents(
        self,
        tenant_id: str,
        chunks: list[tuple[str, int, str]],
    ) -> int:
        """Add document chunks to the knowledge graph.

        Extracts entities from each chunk, creates nodes for both
        chunks and entities, and links them with edges.

        Args:
            tenant_id: Tenant identifier for isolation.
            chunks: List of (document_id, chunk_index, text) tuples.

        Returns:
            Total number of entities extracted.
        """
        graph = self._get_graph(tenant_id)
        total_entities = 0

        for document_id, chunk_index, text in chunks:
            entities = extract_entities(text)
            chunk_id = self._chunk_node_id(document_id, chunk_index)

            graph_chunk = GraphChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                text=text,
                entities=entities,
            )
            self._chunks[tenant_id][chunk_id] = graph_chunk

            graph.add_node(chunk_id, type="chunk", document_id=document_id)

            entity_ids = []
            for entity in entities:
                entity_id = self._entity_node_id(entity)
                graph.add_node(entity_id, type="entity", label=entity.lower())
                graph.add_edge(chunk_id, entity_id)
                entity_ids.append(entity_id)

            # Add co-occurrence edges between entities in the same chunk
            for i, eid_a in enumerate(entity_ids):
                for eid_b in entity_ids[i + 1 :]:
                    if graph.has_edge(eid_a, eid_b):
                        graph[eid_a][eid_b]["weight"] += 1
                    else:
                        graph.add_edge(eid_a, eid_b, weight=1)

            total_entities += len(entities)

        logger.info(
            "knowledge_graph_updated",
            tenant_id=tenant_id,
            chunks_added=len(chunks),
            entities_extracted=total_entities,
            total_nodes=graph.number_of_nodes(),
            total_edges=graph.number_of_edges(),
        )

        return total_entities

    def search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[str, int, str, float]]:
        """Search the knowledge graph by matching query terms to entities.

        Finds entities matching query words, then traverses the graph
        to find connected chunks. Chunks are scored by the number of
        matching entity connections.

        Args:
            tenant_id: Tenant identifier.
            query: Search query text.
            top_k: Maximum number of results to return.

        Returns:
            List of (document_id, chunk_index, text, score) tuples,
            sorted by descending score.
        """
        if tenant_id not in self._graphs:
            return []

        graph = self._graphs[tenant_id]
        query_terms = query.lower().split()

        if not query_terms:
            return []

        # Find entity nodes matching any query term
        matching_entity_ids: set[str] = set()
        for node, data in graph.nodes(data=True):
            if data.get("type") != "entity":
                continue
            label = data.get("label", "")
            if any(term in label for term in query_terms):
                matching_entity_ids.add(node)

        if not matching_entity_ids:
            return []

        # Collect chunks connected to matching entities with scores
        chunk_scores: dict[str, float] = {}
        for entity_id in matching_entity_ids:
            for neighbor in graph.neighbors(entity_id):
                if graph.nodes[neighbor].get("type") == "chunk":
                    chunk_scores[neighbor] = chunk_scores.get(neighbor, 0.0) + 1.0

        # Build results
        results: list[tuple[str, int, str, float]] = []
        for chunk_id, score in chunk_scores.items():
            graph_chunk = self._chunks[tenant_id].get(chunk_id)
            if graph_chunk is not None:
                results.append(
                    (
                        graph_chunk.document_id,
                        graph_chunk.chunk_index,
                        graph_chunk.text,
                        score,
                    )
                )

        results.sort(key=lambda r: r[3], reverse=True)
        return results[:top_k]

    def remove_document(self, tenant_id: str, document_id: str) -> int:
        """Remove all chunks of a document from the graph.

        Removes chunk nodes and cleans up orphaned entity nodes.

        Args:
            tenant_id: Tenant identifier.
            document_id: Document to remove.

        Returns:
            Number of chunk nodes removed.
        """
        if tenant_id not in self._graphs:
            return 0

        graph = self._graphs[tenant_id]

        # Find chunk nodes for this document
        chunk_ids_to_remove = [
            node
            for node, data in graph.nodes(data=True)
            if data.get("type") == "chunk" and data.get("document_id") == document_id
        ]

        if not chunk_ids_to_remove:
            return 0

        for chunk_id in chunk_ids_to_remove:
            graph.remove_node(chunk_id)
            self._chunks[tenant_id].pop(chunk_id, None)

        # Remove orphaned entity nodes (no remaining connections)
        orphaned = [
            node
            for node, data in graph.nodes(data=True)
            if data.get("type") == "entity" and graph.degree(node) == 0
        ]
        graph.remove_nodes_from(orphaned)

        logger.info(
            "knowledge_graph_document_removed",
            tenant_id=tenant_id,
            document_id=document_id,
            chunks_removed=len(chunk_ids_to_remove),
            orphans_cleaned=len(orphaned),
        )

        return len(chunk_ids_to_remove)

    def clear_tenant(self, tenant_id: str) -> None:
        """Remove all data for a tenant (GDPR right to erasure).

        Args:
            tenant_id: Tenant whose data should be deleted.
        """
        self._graphs.pop(tenant_id, None)
        self._chunks.pop(tenant_id, None)
        logger.info("knowledge_graph_tenant_cleared", tenant_id=tenant_id)

    def clear(self) -> None:
        """Remove all data from all graphs."""
        self._graphs.clear()
        self._chunks.clear()
        logger.info("knowledge_graph_all_cleared")
