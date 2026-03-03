"""Embedding service wrapping sentence-transformers for multilingual vectors."""

import numpy as np
import structlog

logger = structlog.get_logger()


class EmbeddingService:
    """Generate vector embeddings using sentence-transformers.

    Uses a multilingual model (default: intfloat/multilingual-e5-large)
    that maps text from any supported language into a shared vector space,
    enabling cross-lingual semantic search.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large") -> None:
        """Initialize with a sentence-transformers model.

        Args:
            model_name: HuggingFace model identifier.
        """
        self._model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy-load the sentence-transformers model on first use."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            logger.info(
                "embedding_model_loaded",
                model=self._model_name,
                vector_size=self.vector_size,
            )
        return self._model

    @property
    def vector_size(self) -> int:
        """Return the dimensionality of embeddings produced by the model."""
        return self.model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Encode texts into vector embeddings.

        Args:
            texts: List of text strings to encode.
            batch_size: Number of texts to process at once.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        if isinstance(embeddings, np.ndarray):
            return embeddings.tolist()
        return [e.tolist() if isinstance(e, np.ndarray) else list(e) for e in embeddings]

    def encode_query(self, query: str) -> list[float]:
        """Encode a single query into a vector embedding.

        Args:
            query: Search query text.

        Returns:
            Embedding vector as a list of floats.
        """
        result = self.encode([query])
        return result[0]
