"""Tests for embedding service."""

from unittest.mock import MagicMock, patch

import numpy as np

from rag_engine.services.embedding import EmbeddingService


class TestEmbeddingService:
    """Tests for the EmbeddingService wrapper."""

    def _make_service_with_mock(self, vector_size: int = 384):
        """Create an EmbeddingService with a mocked model."""
        service = EmbeddingService(model_name="test-model")

        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = vector_size
        service._model = mock_model

        return service, mock_model

    def test_lazy_loading_does_not_load_on_init(self) -> None:
        service = EmbeddingService()
        assert service._model is None

    @patch("rag_engine.services.embedding.logger")
    def test_model_loaded_on_first_access(self, _mock_logger) -> None:
        service, mock_model = self._make_service_with_mock()
        assert service.model is mock_model

    def test_vector_size(self) -> None:
        service, _ = self._make_service_with_mock(vector_size=768)
        assert service.vector_size == 768

    def test_encode_empty_list(self) -> None:
        service, _ = self._make_service_with_mock()
        assert service.encode([]) == []

    def test_encode_returns_list_of_lists(self) -> None:
        service, mock_model = self._make_service_with_mock(vector_size=3)
        mock_model.encode.return_value = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ])

        result = service.encode(["hello", "world"])
        assert len(result) == 2
        assert len(result[0]) == 3
        assert isinstance(result[0], list)
        assert abs(result[0][0] - 0.1) < 1e-6

    def test_encode_passes_correct_params(self) -> None:
        service, mock_model = self._make_service_with_mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2]])

        service.encode(["test"], batch_size=16)
        mock_model.encode.assert_called_once_with(
            ["test"],
            batch_size=16,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

    def test_encode_query_returns_single_vector(self) -> None:
        service, mock_model = self._make_service_with_mock(vector_size=3)
        mock_model.encode.return_value = np.array([[0.7, 0.8, 0.9]])

        result = service.encode_query("search text")
        assert len(result) == 3
        assert isinstance(result, list)
        assert abs(result[0] - 0.7) < 1e-6

    def test_encode_handles_non_ndarray(self) -> None:
        service, mock_model = self._make_service_with_mock()
        # Some models may return list of arrays
        mock_model.encode.return_value = [
            np.array([0.1, 0.2]),
            np.array([0.3, 0.4]),
        ]

        result = service.encode(["a", "b"])
        assert len(result) == 2
        assert isinstance(result[0], list)
