"""Chroma adapter for the VectorStore contract. In-process client (no service).
Lazy import."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from lib.contracts import Chunk, SearchResult


class ChromaStore:
    def __init__(self) -> None:
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import chromadb

            self._client = chromadb.Client()
        return self._client

    def ensure_collection(self, name: str, dim: int) -> None:
        self._get_client().get_or_create_collection(name)

    def upsert(
        self,
        collection: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[list[float]],
    ) -> None:
        col = self._get_client().get_or_create_collection(collection)
        col.upsert(
            ids=[c.id for c in chunks],
            embeddings=[list(v) for v in vectors],
            documents=[c.text for c in chunks],
            metadatas=[{"source": c.source} for c in chunks],
        )

    def delete(self, collection: str, ids: Sequence[str]) -> None:
        self._get_client().get_or_create_collection(collection).delete(ids=list(ids))

    def search(self, collection: str, vector: list[float], k: int = 5) -> list[SearchResult]:
        col = self._get_client().get_or_create_collection(collection)
        res = col.query(query_embeddings=[vector], n_results=k)
        out: list[SearchResult] = []
        for cid, doc, meta, dist in zip(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
            strict=True,
        ):
            chunk = Chunk(id=cid, text=doc, source=str(meta.get("source", "")))
            out.append(SearchResult(chunk=chunk, score=1.0 - float(dist)))
        return out


if TYPE_CHECKING:
    from lib.contracts import VectorStore

    _conforms: type[VectorStore] = ChromaStore
