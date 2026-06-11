"""Zero-dependency in-process vector store: brute-force cosine over Python lists.

The lightest tier — no service, no numpy. Right for tests, CI, and small offline
demos. O(n) search and not persistent, so for real corpora use faiss/chroma/qdrant.
"""

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from lib.contracts import Chunk, SearchResult


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


class MemoryStore:
    def __init__(self) -> None:
        self._cols: dict[str, list[tuple[Chunk, list[float]]]] = {}

    def ensure_collection(self, name: str, dim: int) -> None:
        self._cols.setdefault(name, [])

    def upsert(
        self,
        collection: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[list[float]],
    ) -> None:
        incoming = {c.id: (c, list(v)) for c, v in zip(chunks, vectors, strict=True)}
        kept = [pair for pair in self._cols.get(collection, []) if pair[0].id not in incoming]
        kept.extend(incoming.values())
        self._cols[collection] = kept

    def delete(self, collection: str, ids: Sequence[str]) -> None:
        if collection not in self._cols:
            return
        drop = set(ids)
        self._cols[collection] = [p for p in self._cols[collection] if p[0].id not in drop]

    def search(self, collection: str, vector: list[float], k: int = 5) -> list[SearchResult]:
        scored = [
            SearchResult(chunk=c, score=_cosine(vector, v))
            for c, v in self._cols.get(collection, [])
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:k]


if TYPE_CHECKING:
    from lib.contracts import VectorStore

    _conforms: type[VectorStore] = MemoryStore
