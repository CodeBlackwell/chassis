"""sentence-transformers adapter for the Embedder contract. Serves both the
`minilm` and `bge` registry names (the model is chosen by the `model` kwarg).
The model loads lazily on first use, so importing this module needs no torch."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any


class SbertEmbedder:
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model
        self._model: Any = None

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def dim(self) -> int:
        return int(self._get_model().get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._get_model().encode(list(texts), normalize_embeddings=True)
        return [v.tolist() for v in vectors]


if TYPE_CHECKING:
    from lib.contracts import Embedder

    _conforms: type[Embedder] = SbertEmbedder
