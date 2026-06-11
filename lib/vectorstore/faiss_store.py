"""FAISS adapter for the VectorStore contract. In-process, no service — IndexFlatIP
over normalized vectors gives cosine ranking. Lazy import. Note: upsert appends (no
dedup by id on a flat index); delete removes by position, keeping the parallel
chunk list aligned because remove_ids compacts the index in order.
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from lib.contracts import Chunk, SearchResult


class FaissStore:
    def __init__(self) -> None:
        self._index: dict[str, Any] = {}
        self._chunks: dict[str, list[Chunk]] = {}

    def ensure_collection(self, name: str, dim: int) -> None:
        import faiss

        if name not in self._index:
            self._index[name] = faiss.IndexFlatIP(dim)
            self._chunks[name] = []

    def upsert(
        self,
        collection: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[list[float]],
    ) -> None:
        import numpy as np

        if collection not in self._index:
            self.ensure_collection(collection, len(vectors[0]))
        self._index[collection].add(np.asarray(vectors, dtype="float32"))
        self._chunks[collection].extend(chunks)

    def delete(self, collection: str, ids: Sequence[str]) -> None:
        import numpy as np

        index = self._index.get(collection)
        if index is None:
            return
        drop = set(ids)
        positions = [i for i, c in enumerate(self._chunks[collection]) if c.id in drop]
        if not positions:
            return
        index.remove_ids(np.asarray(positions, dtype="int64"))
        self._chunks[collection] = [c for c in self._chunks[collection] if c.id not in drop]

    def search(self, collection: str, vector: list[float], k: int = 5) -> list[SearchResult]:
        import numpy as np

        index = self._index.get(collection)
        if index is None or index.ntotal == 0:
            return []
        scores, ids = index.search(np.asarray([vector], dtype="float32"), min(k, index.ntotal))
        return [
            SearchResult(chunk=self._chunks[collection][i], score=float(s))
            for s, i in zip(scores[0], ids[0], strict=True)
            if i >= 0
        ]


if TYPE_CHECKING:
    from lib.contracts import VectorStore

    _conforms: type[VectorStore] = FaissStore
