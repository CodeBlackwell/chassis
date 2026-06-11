"""OpenAI adapter for the Embedder contract. text-embedding-3-small is 1536-dim;
that dim is fixed at construction and frozen into the collection at ingest (see
the embedder-dim coupling in docs/architecture/architecture.md). Lazy SDK import."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any


class OpenAIEmbedder:
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        dim: int = 1536,
    ) -> None:
        import os

        self.model = model
        self._dim = dim
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.OpenAI(api_key=self._api_key)
        return self._client

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        resp = self._get_client().embeddings.create(model=self.model, input=list(texts))
        return [item.embedding for item in resp.data]


if TYPE_CHECKING:
    from lib.contracts import Embedder

    _conforms: type[Embedder] = OpenAIEmbedder
