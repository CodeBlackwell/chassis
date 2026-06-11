"""The default Retriever: embed the query, search the vector store. The one piece
of glue between the Embedder and VectorStore contracts. A HybridRetriever (graph
option) plugs in here later behind the same contract.
"""

from typing import TYPE_CHECKING

from config import defaults

from lib.contracts import SearchResult

if TYPE_CHECKING:
    from lib.contracts import Embedder, VectorStore


class SimpleRetriever:
    def __init__(
        self,
        embedder: "Embedder",
        store: "VectorStore",
        collection: str = defaults.CHUNKS_COLLECTION,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._collection = collection

    def retrieve(self, query: str, k: int = defaults.RETRIEVAL_K) -> list[SearchResult]:
        vector = self._embedder.embed([query])[0]
        return self._store.search(self._collection, vector, k=k)


if TYPE_CHECKING:
    from lib.contracts import Retriever

    _conforms: type[Retriever] = SimpleRetriever
