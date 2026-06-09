"""Qdrant adapter for the VectorStore contract. Connects to a running service
(the one store that needs one — drives the docker-compose deployment). Lazy import.
"""

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from lib.contracts import Chunk, SearchResult


class QdrantStore:
    def __init__(self, url: str = "http://localhost:6333") -> None:
        self.url = url
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url)
        return self._client

    def ensure_collection(self, name: str, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if name not in existing:
            client.create_collection(
                name, vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )

    def upsert(
        self,
        collection: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[list[float]],
    ) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, c.id)),
                vector=list(v),
                payload={"id": c.id, "text": c.text, "source": c.source},
            )
            for c, v in zip(chunks, vectors, strict=True)
        ]
        self._get_client().upsert(collection, points)

    def search(self, collection: str, vector: list[float], k: int = 5) -> list[SearchResult]:
        hits = self._get_client().search(collection, query_vector=vector, limit=k)
        out: list[SearchResult] = []
        for hit in hits:
            payload = hit.payload or {}
            chunk = Chunk(
                id=str(payload.get("id", "")),
                text=str(payload.get("text", "")),
                source=str(payload.get("source", "")),
            )
            out.append(SearchResult(chunk=chunk, score=float(hit.score)))
        return out


if TYPE_CHECKING:
    from lib.contracts import VectorStore

    _conforms: type[VectorStore] = QdrantStore
